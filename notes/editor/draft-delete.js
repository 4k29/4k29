(function () {
  "use strict";

  var API_ROOT = "https://api.github.com";
  var API_VERSION = "2022-11-28";
  var DELETED_PATH = "notes/deleted-drafts.json";
  var SESSION_TOKEN_KEY = "4k29-editor-github-token";
  var PERSISTENT_TOKEN_KEY = "4k29-editor-github-token-persistent";
  var STORAGE_KEY = "4k29-note-editor-v1";
  var config = window.EDITOR_GITHUB_CONFIG || {};
  var list = document.getElementById("draft-history-list");
  var historyStatus = document.getElementById("draft-history-status");
  var deletedKeys = new Set();
  var deletedFileSha = "";
  var loaded = false;

  if (!list) return;

  function token() {
    try {
      var persistent = localStorage.getItem(PERSISTENT_TOKEN_KEY) || "";
      if (persistent) return persistent;
    } catch (error) {}
    try {
      return sessionStorage.getItem(SESSION_TOKEN_KEY) || "";
    } catch (error) {
      return "";
    }
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
    if (!response.ok) throw new Error("GitHub API request failed");
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
    return (title ? title.textContent.trim() : "無題の下書き") + "|" + (meta ? meta.textContent.trim() : "");
  }

  function updateVisibleCount() {
    if (!historyStatus) return;
    var count = list.querySelectorAll(".draft-history-item").length;
    historyStatus.textContent = count ? count + "件の下書きを表示しています。" : "復元できる過去の下書きはまだありません。";
  }

  async function loadDeleted() {
    if (loaded) return;
    var file = await request(repoPath("/contents/" + DELETED_PATH + "?ref=" + encodeURIComponent(config.branch || "main")), { allow404: true });
    if (file && file.content) {
      deletedFileSha = file.sha || "";
      try {
        var data = JSON.parse(decodeText(file.content));
        (Array.isArray(data.keys) ? data.keys : []).forEach(function (key) { deletedKeys.add(key); });
      } catch (error) {}
    }
    loaded = true;
  }

  async function saveDeleted() {
    var body = {
      message: "Hide deleted note draft",
      content: encodeText(JSON.stringify({ keys: Array.from(deletedKeys), updatedAt: new Date().toISOString() }, null, 2) + "\n"),
      branch: config.branch || "main"
    };
    if (deletedFileSha) body.sha = deletedFileSha;
    var result = await request(repoPath("/contents/" + DELETED_PATH), { method: "PUT", body: body });
    deletedFileSha = result && result.content ? result.content.sha : deletedFileSha;
  }

  async function clearCurrentDraft() {
    try { localStorage.removeItem(STORAGE_KEY); } catch (error) {}
    if (window.EditorGitHub && window.EditorGitHub.isReady()) {
      await window.EditorGitHub.deleteDraft("notes");
    }
  }

  function decorate() {
    var changed = false;

    Array.from(list.querySelectorAll(".draft-history-item")).forEach(function (item) {
      if (item.dataset.deleteReady === "true") return;
      item.dataset.deleteReady = "true";
      var key = itemKey(item);
      if (deletedKeys.has(key)) {
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
          deletedKeys.add(key);
          await saveDeleted();
          var isCurrent = Boolean(item.querySelector(".draft-history-current"));
          if (isCurrent) await clearCurrentDraft();
          row.remove();
          updateVisibleCount();
          if (isCurrent) location.reload();
        } catch (error) {
          deletedKeys.delete(key);
          remove.disabled = false;
          if (historyStatus) historyStatus.textContent = "下書きを削除できませんでした。通信状況を確認してください。";
        }
      });
    });

    if (changed && loaded) updateVisibleCount();
  }

  loadDeleted().then(function () {
    decorate();
    updateVisibleCount();
    new MutationObserver(decorate).observe(list, { childList: true });
  }).catch(function () {
    new MutationObserver(decorate).observe(list, { childList: true });
  });
}());
