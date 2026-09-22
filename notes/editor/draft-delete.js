(function () {
  "use strict";

  var API_ROOT = "https://api.github.com";
  var API_VERSION = "2022-11-28";
  var DELETED_PATH = "notes/deleted-drafts.json";
  var STORAGE_KEY = "4k29-note-editor-v1";
  var config = window.EDITOR_GITHUB_CONFIG || {};
  var list = document.getElementById("draft-history-list");
  var historyStatus = document.getElementById("draft-history-status");
  var deletedKeys = new Set();
  var deletionQueue = Promise.resolve();
  var loaded = false;


  if (!list) return;

  function token() {
    return window.EditorGitHub && window.EditorGitHub.getToken
      ? window.EditorGitHub.getToken() : "";
  }

  function repoPath(suffix) {
    return "/repos/" + encodeURIComponent(config.owner) + "/" + encodeURIComponent(config.repository) + suffix;
  }

  async function request(path, options) {
    options = options || {};
    var response = await fetch(API_ROOT + path, {
      method: options.method || "GET",
      headers: {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token(),
        "X-GitHub-Api-Version": API_VERSION,
        "Content-Type": "application/json"
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
      cache: "no-store",
      credentials: "omit"
    });
    if (options.allow404 && response.status === 404) return null;
    if (!response.ok) {
      var error = new Error("GitHub API request failed");
      error.status = response.status;
      throw error;
    }
    return response.status === 204 ? null : response.json();
  }

  function encodeText(value) {
    var bytes = new TextEncoder().encode(value);
    var binary = "";
    bytes.forEach(function (byte) { binary += String.fromCharCode(byte); });
    return btoa(binary);
  }

  function decodeText(value) {
    var binary = atob(String(value || "").replace(/\s/g, ""));
    var bytes = new Uint8Array(binary.length);
    for (var i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    return new TextDecoder("utf-8").decode(bytes);
  }

  function itemKey(item) {
    var title = item.querySelector("strong");
    var meta = item.querySelector(".draft-history-meta");
    return item.dataset.draftIdentity || (title ? title.textContent.trim() : "無題の下書き") + "|" + (meta ? meta.textContent.trim() : "");
  }

  function updateVisibleCount() {
    if (!historyStatus) return;
    var count = list.querySelectorAll(".draft-history-item").length;
    historyStatus.textContent = count ? count + "件の下書きを表示しています。" : "復元できる過去の下書きはまだありません。";
  }

  async function readDeleted() {
    var file = await request(repoPath("/contents/" + DELETED_PATH + "?ref=" + encodeURIComponent(config.branch || "main")), { allow404: true });
    var keys = [];
    if (file && file.content) {
      var data = JSON.parse(decodeText(file.content));
      if (!Array.isArray(data.keys)) throw new Error("Invalid deleted draft list");
      keys = data.keys;
    }
    return { keys: keys, sha: file && file.sha };
  }

  async function loadDeleted() {
    var state = await readDeleted();
    deletedKeys = new Set(state.keys);
    loaded = true;
  }

  function saveDeleted(key) {
    var operation = deletionQueue.then(async function () {
      for (var attempt = 0; attempt < 3; attempt += 1) {
        // Always read the latest version; another tab may have deleted a draft.
        var state = await readDeleted();
        var keys = new Set(state.keys);
        keys.add(key);
        var body = {
          message: "Hide deleted note draft",
          content: encodeText(JSON.stringify({ keys: Array.from(keys), updatedAt: new Date().toISOString() }, null, 2) + "\n"),
          branch: config.branch || "main"
        };
        if (state.sha) body.sha = state.sha;
        try {
          await request(repoPath("/contents/" + DELETED_PATH), { method: "PUT", body: body });
          deletedKeys = keys;
          loaded = true;
          return;
        } catch (error) {
          if (attempt < 2 && (error.status === 409 || error.status === 422)) continue;
          throw error;
        }
      }
    });
    deletionQueue = operation.catch(function () {});
    return operation;
  }

  function clearCurrentDraft() {
    try { localStorage.removeItem(STORAGE_KEY); } catch (error) {}
    // current.json is a shared history pointer, not necessarily the open draft.
    window.dispatchEvent(new CustomEvent("notedraftdeleted"));
  }

  function errorMessage(error) {
    if (error.status === 401) return "GitHubの認証が切れています。ログインし直してください。";
    if (error.status === 403 || error.status === 404) return "下書き保存先へのアクセス権限を確認してください。GitHubの利用制限の可能性もあります。";
    if (error.status === 409 || error.status === 422) return "別の保存処理と重なりました。もう一度削除してください。";
    return "下書きを削除できませんでした。通信状況を確認して再試行してください。";
  }

  function decorate() {
    if (!loaded) return;

    var changed = false;

    Array.from(list.querySelectorAll(".draft-history-item")).forEach(function (item) {
      if (item.dataset.deleteReady === "true") return;
      item.dataset.deleteReady = "true";
      var key = itemKey(item);
      var legacyKey = (item.querySelector("strong") ? item.querySelector("strong").textContent.trim() : "無題の下書き") + "|" + (item.querySelector(".draft-history-meta") ? item.querySelector(".draft-history-meta").textContent.trim() : "");
      if (deletedKeys.has(key) || deletedKeys.has(legacyKey)) {
        item.remove();
        changed = true;
        return;
      }

      var row = document.createElement("div");
      row.className = "draft-history-row";
      item.parentNode.insertBefore(row, item);
      row.appendChild(item);

      var remove = document.createElement("button");
      remove.type = "button";
      remove.className = "draft-history-delete";
      remove.textContent = "削除";
      remove.setAttribute("aria-label", "「" + (item.querySelector("strong") ? item.querySelector("strong").textContent : "下書き") + "」を削除");
      row.appendChild(remove);
      changed = true;

      remove.addEventListener("click", async function () {
        var title = item.querySelector("strong") ? item.querySelector("strong").textContent : "この下書き";
        if (!confirm("「" + title + "」を下書き一覧から削除しますか？")) return;
        remove.disabled = true;
        if (historyStatus) historyStatus.textContent = "下書きを削除しています…";
        try {
          await saveDeleted(key);
          var isCurrent = Boolean(item.querySelector(".draft-history-current"));
          if (isCurrent) await clearCurrentDraft();
          row.remove();
          updateVisibleCount();
        } catch (error) {
          remove.disabled = false;
          if (historyStatus) historyStatus.textContent = errorMessage(error);
        }
      });
    });

    if (changed && loaded) updateVisibleCount();
  }

  if (window.EditorGitHub) {
    window.EditorGitHub.onReady(async function () {
      new MutationObserver(decorate).observe(list, { childList: true });
      try {
        await loadDeleted();
      } catch (error) {
        // A later deletion retries the read; never write using an unknown SHA.
        loaded = true;
        if (historyStatus) historyStatus.textContent = errorMessage(error);
      }
      decorate();
    });
  }
}());
