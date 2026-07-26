(function () {
  "use strict";

  var EDITOR = "memory";
  var DRAFT_PATH = "memory/current.json";
  var DELETED_PATH = "memory/deleted-drafts.json";
  var API_ROOT = "https://api.github.com";
  var API_VERSION = "2022-11-28";
  var SESSION_TOKEN_KEY = "4k29-editor-github-token";
  var PERSISTENT_TOKEN_KEY = "4k29-editor-github-token-persistent";
  var DB_NAME = "4k29-memory-editor-v1";
  var DB_STORE = "drafts";
  var DB_KEY = "current";
  var MAX_RESULTS = 18;
  var COMMITS_PER_PAGE = 30;
  var MAX_PAGES = 4;

  var config = window.EDITOR_GITHUB_CONFIG || {};
  var form = document.getElementById("memory-form");
  var titleField = document.getElementById("title");
  var slugField = document.getElementById("slug");
  var descriptionField = document.getElementById("description");
  var photoList = document.getElementById("photo-list");
  var editorStatus = document.getElementById("save-status");
  var saveButton = document.getElementById("save-now-button");
  var draftsButton = document.getElementById("drafts-button");
  var newButton = document.getElementById("new-button");
  var dialog = document.getElementById("draft-history-dialog");
  var closeButton = document.getElementById("draft-history-close");
  var refreshButton = document.getElementById("draft-history-refresh");
  var historyStatus = document.getElementById("draft-history-status");
  var list = document.getElementById("draft-history-list");
  var deletedKeys = new Set();
  var deletedFileSha = "";
  var historyLoaded = false;
  var loading = false;
  var saving = false;

  if (!form || !draftsButton || !dialog || !list) return;

  function storedToken() {
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
    return "/repos/" + encodeURIComponent(config.owner) + "/" + encodeURIComponent(config.repository) + (suffix || "");
  }

  async function request(path, options) {
    options = options || {};
    var token = storedToken();
    if (!token) throw new Error("GitHub token is unavailable");

    var response = await fetch(API_ROOT + path, {
      method: options.method || "GET",
      headers: {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
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
    bytes.forEach(function (byte) {
      binary += String.fromCharCode(byte);
    });
    return btoa(binary);
  }

  function decodeText(value) {
    var binary = atob(String(value || "").replace(/\s/g, ""));
    var bytes = new Uint8Array(binary.length);
    for (var index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    return new TextDecoder("utf-8").decode(bytes);
  }

  function metadataOf(data) {
    return data && data.metadata ? data.metadata : {};
  }

  function hasDraftContent(data) {
    var metadata = metadataOf(data);
    return Boolean(metadata.title || metadata.description || (data && Array.isArray(data.photos) && data.photos.length));
  }

  function draftIdentity(data, fallback) {
    var metadata = metadataOf(data);
    var slug = String(metadata.slug || "").trim().toLowerCase();
    if (slug) return "slug:" + slug;
    var title = String(metadata.title || "").trim().toLowerCase();
    if (title) return "title:" + title;
    return "commit:" + fallback;
  }

  function currentIdentity() {
    return draftIdentity({
      metadata: {
        title: titleField ? titleField.value.trim() : "",
        slug: slugField ? slugField.value.trim() : ""
      }
    }, "current");
  }

  function commitDate(commit) {
    var details = commit && commit.commit;
    return (details && details.committer && details.committer.date) ||
      (details && details.author && details.author.date) || "";
  }

  async function readFileAt(path, ref) {
    return request(
      repoPath("/contents/" + path.split("/").map(encodeURIComponent).join("/") + "?ref=" + encodeURIComponent(ref)),
      { allow404: true }
    );
  }

  async function readDraftAtRef(ref) {
    var file = await readFileAt(DRAFT_PATH, ref);
    if (!file || !file.content) return null;
    try {
      return JSON.parse(decodeText(file.content));
    } catch (error) {
      return null;
    }
  }

  async function snapshotFromCommit(commit) {
    var data = await readDraftAtRef(commit.sha);
    var sourceRef = commit.sha;

    if (!data && commit.parents && commit.parents[0]) {
      sourceRef = commit.parents[0].sha;
      data = await readDraftAtRef(sourceRef);
    }
    if (!hasDraftContent(data)) return null;

    var key = draftIdentity(data, sourceRef);
    if (deletedKeys.has(key)) return null;

    return {
      data: data,
      key: key,
      sourceRef: sourceRef,
      updatedAt: data.updatedAt || commitDate(commit)
    };
  }

  async function loadDeletedKeys() {
    var file = await readFileAt(DELETED_PATH, config.branch || "main");
    if (!file || !file.content) return;
    deletedFileSha = file.sha || "";
    try {
      var data = JSON.parse(decodeText(file.content));
      (Array.isArray(data.keys) ? data.keys : []).forEach(function (key) {
        deletedKeys.add(key);
      });
    } catch (error) {}
  }

  async function saveDeletedKeys() {
    var body = {
      message: "Hide deleted memory draft",
      content: encodeText(JSON.stringify({
        keys: Array.from(deletedKeys),
        updatedAt: new Date().toISOString()
      }, null, 2) + "\n"),
      branch: config.branch || "main"
    };
    if (deletedFileSha) body.sha = deletedFileSha;

    var result = await request(repoPath("/contents/" + DELETED_PATH), {
      method: "PUT",
      body: body
    });
    deletedFileSha = result && result.content ? result.content.sha : deletedFileSha;
  }

  async function fetchHistory() {
    await loadDeletedKeys();
    var results = [];
    var seen = new Set();

    for (var page = 1; page <= MAX_PAGES && results.length < MAX_RESULTS; page += 1) {
      var commits = await request(
        repoPath("/commits?path=" + encodeURIComponent(DRAFT_PATH) +
          "&sha=" + encodeURIComponent(config.branch || "main") +
          "&per_page=" + COMMITS_PER_PAGE + "&page=" + page)
      );
      if (!Array.isArray(commits) || !commits.length) break;

      for (var start = 0; start < commits.length && results.length < MAX_RESULTS; start += 4) {
        var snapshots = await Promise.all(commits.slice(start, start + 4).map(snapshotFromCommit));
        snapshots.forEach(function (snapshot) {
          if (!snapshot || seen.has(snapshot.key) || results.length >= MAX_RESULTS) return;
          seen.add(snapshot.key);
          results.push(snapshot);
        });
      }
      if (commits.length < COMMITS_PER_PAGE) break;
    }
    return results;
  }

  function formatDateTime(value) {
    if (!value) return "保存日時不明";
    var date = new Date(value);
    if (Number.isNaN(date.getTime())) return "保存日時不明";
    return new Intl.DateTimeFormat("ja-JP", {
      timeZone: "Asia/Tokyo",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit"
    }).format(date);
  }

  function hasCurrentContent() {
    return Boolean(
      (titleField && titleField.value.trim()) ||
      (descriptionField && descriptionField.value.trim()) ||
      (photoList && photoList.children.length)
    );
  }

  function savedStatus(text) {
    return /GitHubに(保存|同期)済み|端末内に保存済み|GitHubに接続済み/.test(text || "");
  }

  function failedStatus(text) {
    return /未同期|できません|失敗/.test(text || "");
  }

  function waitForSave(timeout) {
    return new Promise(function (resolve, reject) {
      var started = Date.now();
      var timer = window.setInterval(function () {
        var text = editorStatus ? editorStatus.textContent : "";
        if (savedStatus(text)) {
          window.clearInterval(timer);
          resolve();
          return;
        }
        if (failedStatus(text)) {
          window.clearInterval(timer);
          reject(new Error(text));
          return;
        }
        if (Date.now() - started > timeout) {
          window.clearInterval(timer);
          reject(new Error("保存の完了を確認できませんでした"));
        }
      }, 180);
    });
  }

  async function saveCurrentDraft() {
    if (!hasCurrentContent()) {
      if (editorStatus) editorStatus.textContent = "保存する内容がありません";
      return;
    }
    if (saving) return waitForSave(9000);
    saving = true;
    try {
      if (editorStatus) editorStatus.textContent = "保存中…";
      (titleField || form).dispatchEvent(new Event("input", { bubbles: true }));
      await waitForSave(9000);
      if (editorStatus && /GitHubに保存済み/.test(editorStatus.textContent)) {
        editorStatus.textContent = "✓ GitHubに同期済み";
      }
    } finally {
      saving = false;
    }
  }

  async function writeFile(path, content, message) {
    var current = await readFileAt(path, config.branch || "main");
    var body = {
      message: message,
      content: content,
      branch: config.branch || "main"
    };
    if (current && current.sha) body.sha = current.sha;
    return request(repoPath("/contents/" + path.split("/").map(encodeURIComponent).join("/")), {
      method: "PUT",
      body: body
    });
  }

  async function restorePhotoFile(photo, sourceRef) {
    if (!photo || !photo.githubPath) return;
    var historical = await readFileAt(photo.githubPath, sourceRef);
    if (!historical || !historical.content) {
      var current = await readFileAt(photo.githubPath, config.branch || "main");
      if (current) return;
      throw new Error("写真を復元できませんでした");
    }

    var currentFile = await readFileAt(photo.githubPath, config.branch || "main");
    if (currentFile && currentFile.sha === historical.sha) return;
    await writeFile(photo.githubPath, historical.content.replace(/\s/g, ""), "Restore memory draft photo");
  }

  async function restorePhotos(record) {
    var photos = Array.isArray(record.data.photos) ? record.data.photos : [];
    for (var start = 0; start < photos.length; start += 3) {
      if (historyStatus) {
        historyStatus.textContent = "写真を復元しています… " + Math.min(start + 3, photos.length) + " / " + photos.length;
      }
      await Promise.all(photos.slice(start, start + 3).map(function (photo) {
        return restorePhotoFile(photo, record.sourceRef);
      }));
    }
  }

  async function openDraft(record) {
    await saveCurrentDraft();
    await restorePhotos(record);

    var restoredData = JSON.parse(JSON.stringify(record.data));
    restoredData.updatedAt = new Date().toISOString();
    await writeFile(
      DRAFT_PATH,
      encodeText(JSON.stringify(restoredData, null, 2) + "\n"),
      "Open memory draft " + (metadataOf(restoredData).title || "Untitled")
    );
    window.location.reload();
  }

  function clearLocalDraft() {
    return new Promise(function (resolve) {
      if (!("indexedDB" in window)) {
        resolve();
        return;
      }
      var open = indexedDB.open(DB_NAME, 1);
      open.onerror = function () { resolve(); };
      open.onsuccess = function () {
        var database = open.result;
        if (!database.objectStoreNames.contains(DB_STORE)) {
          database.close();
          resolve();
          return;
        }
        var transaction = database.transaction(DB_STORE, "readwrite");
        transaction.objectStore(DB_STORE).delete(DB_KEY);
        transaction.oncomplete = function () {
          database.close();
          resolve();
        };
        transaction.onerror = function () {
          database.close();
          resolve();
        };
      };
    });
  }

  async function deleteCurrentDraftOnly() {
    if (window.EditorGitHub && window.EditorGitHub.isReady()) {
      await window.EditorGitHub.deleteDraft(EDITOR);
    }
    await clearLocalDraft();
  }

  function renderHistory(records) {
    list.innerHTML = "";
    var activeIdentity = currentIdentity();

    if (!records.length) {
      var empty = document.createElement("p");
      empty.className = "memory-draft-empty";
      empty.textContent = "復元できる過去の下書きはまだありません。";
      list.appendChild(empty);
      return;
    }

    records.forEach(function (record) {
      var metadata = metadataOf(record.data);
      var row = document.createElement("div");
      row.className = "memory-draft-row";

      var item = document.createElement("button");
      item.type = "button";
      item.className = "memory-draft-item";

      var heading = document.createElement("span");
      heading.className = "memory-draft-heading";
      var title = document.createElement("strong");
      title.textContent = metadata.title || "無題のMemory";
      heading.appendChild(title);

      var isCurrent = record.key === activeIdentity;
      if (isCurrent) {
        var badge = document.createElement("span");
        badge.className = "memory-draft-current";
        badge.textContent = "現在";
        heading.appendChild(badge);
      }

      var meta = document.createElement("span");
      meta.className = "memory-draft-meta";
      var shownDate = metadata.dateDisplay || metadata.date || "日付未設定";
      var photoTotal = Array.isArray(record.data.photos) ? record.data.photos.length : 0;
      meta.textContent = shownDate + " / " + photoTotal + "枚 / " + formatDateTime(record.updatedAt) + " 保存";

      var summary = document.createElement("span");
      summary.className = "memory-draft-summary";
      summary.textContent = metadata.description || "概要はまだありません。";

      item.append(heading, meta, summary);
      item.addEventListener("click", async function () {
        if (item.disabled) return;
        item.disabled = true;
        if (historyStatus) historyStatus.textContent = "現在の内容を保存して、下書きを開いています…";
        try {
          await openDraft(record);
        } catch (error) {
          item.disabled = false;
          if (historyStatus) historyStatus.textContent = "下書きを開けませんでした。写真または通信状況を確認してください。";
        }
      });

      var remove = document.createElement("button");
      remove.type = "button";
      remove.className = "memory-draft-delete";
      remove.textContent = "削除";
      remove.setAttribute("aria-label", "「" + title.textContent + "」を削除");
      remove.addEventListener("click", async function () {
        if (!confirm("「" + title.textContent + "」を下書き一覧から削除しますか？")) return;
        remove.disabled = true;
        if (historyStatus) historyStatus.textContent = "下書きを削除しています…";
        try {
          deletedKeys.add(record.key);
          await saveDeletedKeys();
          if (isCurrent) {
            await deleteCurrentDraftOnly();
            window.location.reload();
            return;
          }
          row.remove();
          if (historyStatus) historyStatus.textContent = "下書きを削除しました。";
        } catch (error) {
          deletedKeys.delete(record.key);
          remove.disabled = false;
          if (historyStatus) historyStatus.textContent = "下書きを削除できませんでした。通信状況を確認してください。";
        }
      });

      row.append(item, remove);
      list.appendChild(row);
    });
  }

  async function loadAndRender(force) {
    if (loading || (historyLoaded && !force)) return;
    loading = true;
    if (refreshButton) refreshButton.disabled = true;
    list.innerHTML = "";
    if (historyStatus) historyStatus.textContent = "GitHubから過去の下書きを確認中…";

    try {
      var records = await fetchHistory();
      renderHistory(records);
      historyLoaded = true;
      if (historyStatus) historyStatus.textContent = records.length + "件の下書きを表示しています。";
    } catch (error) {
      if (historyStatus) historyStatus.textContent = "下書き履歴を読み込めませんでした。通信状況を確認してください。";
    } finally {
      loading = false;
      if (refreshButton) refreshButton.disabled = false;
    }
  }

  if (saveButton) {
    saveButton.disabled = true;
    saveButton.addEventListener("click", async function () {
      if (saveButton.disabled || saving) return;
      saveButton.disabled = true;
      try {
        await saveCurrentDraft();
      } catch (error) {
        if (editorStatus) editorStatus.textContent = "端末内に保存済み・GitHub未同期";
      } finally {
        saveButton.disabled = false;
      }
    });
  }

  draftsButton.disabled = true;
  draftsButton.addEventListener("click", function () {
    dialog.showModal();
    loadAndRender(false);
  });
  if (closeButton) closeButton.addEventListener("click", function () { dialog.close(); });
  if (refreshButton) refreshButton.addEventListener("click", function () {
    historyLoaded = false;
    loadAndRender(true);
  });
  dialog.addEventListener("click", function (event) {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener("cancel", function (event) {
    event.preventDefault();
    dialog.close();
  });

  if (newButton) {
    newButton.addEventListener("click", async function (event) {
      event.preventDefault();
      event.stopImmediatePropagation();
      if (!confirm("現在の下書きを履歴に残して、新しいMemoryを作成しますか？")) return;
      newButton.disabled = true;
      try {
        if (hasCurrentContent()) await saveCurrentDraft();
        await deleteCurrentDraftOnly();
        window.location.reload();
      } catch (error) {
        newButton.disabled = false;
        if (editorStatus) editorStatus.textContent = "新しい下書きを作成できませんでした";
      }
    }, true);
  }

  if (window.EditorGitHub) {
    window.EditorGitHub.onReady(function () {
      draftsButton.disabled = false;
      if (saveButton) saveButton.disabled = false;
    });
  }
}());
