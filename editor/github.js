(function () {
  "use strict";

  var config = window.EDITOR_GITHUB_CONFIG || {};
  var SESSION_TOKEN_KEY = "4k29-editor-github-token";
  var PERSISTENT_TOKEN_KEY = "4k29-editor-github-token-persistent";
  var API_ROOT = "https://api.github.com";
  var API_VERSION = "2022-11-28";
  var token = "";
  var user = null;
  var repository = null;
  var branch = "";
  var ready = false;
  var initialized = false;
  var readyCallbacks = [];
  var gate = null;
  var account = null;
  var writeQueue = Promise.resolve();

  var editorApi = {
    onReady: onReady,
    isReady: function () {
      return ready && Boolean(token && user && repository);
    },
    getUser: function () {
      return user;
    },
    loadDraft: loadDraft,
    saveDraft: saveDraft,
    deleteDraft: deleteDraft,
    downloadDraftFile: downloadDraftFile,
    signOut: signOut
  };

  window.EditorGitHub = editorApi;

  function configured() {
    return /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$/.test(config.owner || "") &&
      /^[A-Za-z0-9._-]+$/.test(config.repository || "") &&
      Boolean(config.branch);
  }

  function createGate() {
    if (gate) return;
    gate = document.createElement("div");
    gate.className = "editor-github-gate";
    gate.setAttribute("role", "dialog");
    gate.setAttribute("aria-modal", "true");
    gate.setAttribute("aria-labelledby", "editor-github-title");
    document.body.appendChild(gate);
  }

  function gateContent(kicker, title, message) {
    createGate();
    gate.innerHTML = "";
    var card = document.createElement("section");
    card.className = "editor-github-card";

    var label = document.createElement("p");
    label.className = "editor-github-kicker";
    label.textContent = kicker;

    var heading = document.createElement("h1");
    heading.id = "editor-github-title";
    heading.textContent = title;

    var copy = document.createElement("p");
    copy.className = "editor-github-message";
    copy.textContent = message;

    card.append(label, heading, copy);
    gate.appendChild(card);
    return card;
  }

  function addSetupLink(card) {
    var link = document.createElement("a");
    link.className = "editor-github-help";
    link.href = config.setupUrl || "/4k29/editor/setup/";
    link.textContent = "初回設定のやり方を見る";
    card.appendChild(link);
  }

  function showSetupRequired() {
    var card = gateContent(
      "GitHub setup",
      "初期設定が必要です",
      "GitHubの下書き保存先が設定されていません。設定が完了するまで、このエディターはロックされています。"
    );
    addSetupLink(card);
  }

  function showLogin(message) {
    var card = gateContent(
      "Private editor",
      "GitHubで本人確認",
      message || "下書き専用リポジトリにだけ使えるGitHubキーを入力してください。本人確認後、この端末に安全に保存します。"
    );
    var form = document.createElement("form");
    form.className = "editor-github-form";

    var label = document.createElement("label");
    label.setAttribute("for", "editor-github-token");
    label.textContent = "Fine-grained personal access token";

    var input = document.createElement("input");
    input.id = "editor-github-token";
    input.type = "password";
    input.autocomplete = "off";
    input.autocapitalize = "none";
    input.spellcheck = false;
    input.placeholder = "github_pat_…";
    input.required = true;

    var button = document.createElement("button");
    button.type = "submit";
    button.textContent = "確認してエディターを開く";

    var result = document.createElement("p");
    result.className = "editor-github-result";
    result.setAttribute("role", "status");
    result.setAttribute("aria-live", "polite");

    label.appendChild(input);
    form.append(label, button, result);
    card.appendChild(form);
    addSetupLink(card);
    input.focus();

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      button.disabled = true;
      result.textContent = "GitHubアカウントと保存先を確認中…";
      token = input.value.trim();

      try {
        await verifyAccess();
        savePersistentToken(token);
        unlock();
        notifyReady();
      } catch (error) {
        clearStoredToken();
        token = "";
        button.disabled = false;
        result.textContent = accessErrorMessage(error);
        input.select();
      }
    });
  }

  function showLoading() {
    gateContent("Private editor", "確認中…", "GitHubアカウントと下書き保存先を確認しています。");
  }

  function accessErrorMessage(error) {
    if (error && error.editorCode === "wrong-owner") {
      return "@" + config.owner + " のGitHubキーではありません。別のアカウントのキーでは開けません。";
    }
    if (error && error.editorCode === "public-repository") {
      return "下書きリポジトリがPublicです。Privateへ変更してから、もう一度確認してください。";
    }
    if (error && error.status === 404) {
      return "非公開リポジトリ「" + config.repository + "」を確認できません。作成とキーの対象リポジトリを確認してください。";
    }
    if (error && (error.status === 401 || error.status === 403)) {
      return "キーが無効か、ContentsのRead and write権限がありません。設定を確認してください。";
    }
    return "GitHubへ接続できませんでした。通信状況と初期設定を確認してください。";
  }

  function showAccount() {
    if (account) account.remove();
    account = document.createElement("aside");
    account.className = "editor-github-account";

    var text = document.createElement("span");
    text.textContent = "GitHub / @" + user.login;

    var button = document.createElement("button");
    button.type = "button";
    button.textContent = "ログアウト";
    button.addEventListener("click", signOut);

    account.append(text, button);
    document.body.appendChild(account);
  }

  function unlock() {
    document.documentElement.classList.remove("editor-github-locked");
    if (gate) gate.remove();
    gate = null;
    showAccount();
  }

  function lock() {
    document.documentElement.classList.add("editor-github-locked");
    if (account) account.remove();
    account = null;
    createGate();
  }

  function onReady(callback) {
    if (typeof callback !== "function") return;
    if (ready) {
      callback(editorApi);
      return;
    }
    readyCallbacks.push(callback);
  }

  function notifyReady() {
    if (ready) return;
    ready = true;
    var callbacks = readyCallbacks.slice();
    readyCallbacks = [];
    callbacks.forEach(function (callback) {
      try {
        callback(editorApi);
      } catch (error) {
        window.setTimeout(function () {
          throw error;
        }, 0);
      }
    });
    window.dispatchEvent(new CustomEvent("editorgithubready", { detail: editorApi }));
  }

  function savePersistentToken(value) {
    try {
      window.localStorage.setItem(PERSISTENT_TOKEN_KEY, value);
      window.sessionStorage.removeItem(SESSION_TOKEN_KEY);
    } catch (error) {
      try {
        window.sessionStorage.setItem(SESSION_TOKEN_KEY, value);
      } catch (sessionError) {
        return;
      }
    }
  }

  function readStoredToken() {
    try {
      var persistentToken = window.localStorage.getItem(PERSISTENT_TOKEN_KEY) || "";
      if (persistentToken) return persistentToken;
    } catch (error) {
      // Fall back to the current tab when persistent storage is unavailable.
    }
    try {
      return window.sessionStorage.getItem(SESSION_TOKEN_KEY) || "";
    } catch (error) {
      return "";
    }
  }

  function clearStoredToken() {
    try {
      window.localStorage.removeItem(PERSISTENT_TOKEN_KEY);
    } catch (error) {
      // Continue and clear the current tab as well.
    }
    try {
      window.sessionStorage.removeItem(SESSION_TOKEN_KEY);
    } catch (error) {
      return;
    }
  }

  async function verifyAccess() {
    user = await apiRequest("/user");
    if (!user || String(user.login).toLowerCase() !== String(config.owner).toLowerCase()) {
      var ownerError = new Error("Wrong GitHub owner");
      ownerError.editorCode = "wrong-owner";
      throw ownerError;
    }

    repository = await apiRequest(repoPath(""));
    if (repository.private !== true) {
      var privateError = new Error("Draft repository must be private");
      privateError.editorCode = "public-repository";
      throw privateError;
    }
    branch = config.branch || repository.default_branch;
    await apiRequest(repoPath("/git/ref/heads/" + encodeURIComponent(branch)));
  }

  function requireReady() {
    if (!editorApi.isReady()) throw new Error("GitHub editor is not ready");
  }

  function repoPath(suffix) {
    return "/repos/" + encodeURIComponent(config.owner) + "/" + encodeURIComponent(config.repository) + (suffix || "");
  }

  async function apiRequest(path, options) {
    options = options || {};
    var headers = {
      "Accept": options.accept || "application/vnd.github+json",
      "Authorization": "Bearer " + token,
      "X-GitHub-Api-Version": API_VERSION
    };
    if (options.body !== undefined) headers["Content-Type"] = "application/json";

    var response = await window.fetch(API_ROOT + path, {
      method: options.method || "GET",
      headers: headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      cache: "no-store",
      credentials: "omit"
    });

    if (options.allow404 && response.status === 404) return null;
    if (!response.ok) {
      var details = null;
      try {
        details = await response.json();
      } catch (error) {
        details = null;
      }
      var requestError = new Error(details && details.message ? details.message : "GitHub API request failed");
      requestError.status = response.status;
      requestError.details = details;
      throw requestError;
    }
    if (options.raw) return response.blob();
    if (response.status === 204) return null;
    return response.json();
  }

  function encodeRepositoryPath(path) {
    return String(path).split("/").map(encodeURIComponent).join("/");
  }

  function validateEditor(editor) {
    if (editor !== "notes" && editor !== "memory") {
      throw new Error("Unknown editor");
    }
  }

  function validateDraftPath(editor, path) {
    var value = String(path || "");
    if (!value.startsWith(editor + "/") || value.includes("..") || !/^[A-Za-z0-9._/-]+$/.test(value)) {
      throw new Error("Invalid draft path");
    }
    return value;
  }

  function decodeBase64Text(value) {
    var binary = window.atob(String(value || "").replace(/\s/g, ""));
    var bytes = new Uint8Array(binary.length);
    for (var index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    return new TextDecoder("utf-8").decode(bytes);
  }

  function blobToBase64(blob) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onerror = function () {
        reject(reader.error || new Error("Could not read draft file"));
      };
      reader.onload = function () {
        resolve(String(reader.result).split(",")[1] || "");
      };
      reader.readAsDataURL(blob);
    });
  }

  async function mapWithLimit(items, limit, callback) {
    var results = new Array(items.length);
    var nextIndex = 0;

    async function worker() {
      while (nextIndex < items.length) {
        var index = nextIndex;
        nextIndex += 1;
        results[index] = await callback(items[index], index);
      }
    }

    var workers = [];
    var count = Math.min(limit, items.length);
    for (var index = 0; index < count; index += 1) workers.push(worker());
    await Promise.all(workers);
    return results;
  }

  async function prepareTreeEntries(entries) {
    var unique = new Map();
    entries.forEach(function (entry) {
      unique.set(entry.path, entry);
    });

    return mapWithLimit(Array.from(unique.values()), 4, async function (entry) {
      if (entry.delete) {
        return {
          path: entry.path,
          mode: "100644",
          type: "blob",
          sha: null,
          delete: true
        };
      }

      var body;
      if (entry.blob) {
        body = {
          content: await blobToBase64(entry.blob),
          encoding: "base64"
        };
      } else {
        body = {
          content: String(entry.content || ""),
          encoding: "utf-8"
        };
      }
      var created = await apiRequest(repoPath("/git/blobs"), {
        method: "POST",
        body: body
      });
      return {
        path: entry.path,
        mode: "100644",
        type: "blob",
        sha: created.sha,
        delete: false
      };
    });
  }

  async function repositoryState() {
    var reference = await apiRequest(repoPath("/git/ref/heads/" + encodeURIComponent(branch)));
    var commit = await apiRequest(repoPath("/git/commits/" + reference.object.sha));
    var tree = await apiRequest(repoPath("/git/trees/" + commit.tree.sha + "?recursive=1"));
    return {
      headSha: reference.object.sha,
      treeSha: commit.tree.sha,
      existingPaths: new Set((tree.tree || []).map(function (item) {
        return item.path;
      }))
    };
  }

  async function commitPreparedEntries(prepared, message) {
    for (var attempt = 0; attempt < 2; attempt += 1) {
      var state = await repositoryState();
      var treeEntries = prepared.filter(function (entry) {
        return !entry.delete || state.existingPaths.has(entry.path);
      }).map(function (entry) {
        return {
          path: entry.path,
          mode: entry.mode,
          type: entry.type,
          sha: entry.sha
        };
      });

      if (!treeEntries.length) return null;
      var tree = await apiRequest(repoPath("/git/trees"), {
        method: "POST",
        body: {
          base_tree: state.treeSha,
          tree: treeEntries
        }
      });
      if (tree.sha === state.treeSha) return null;

      var commit = await apiRequest(repoPath("/git/commits"), {
        method: "POST",
        body: {
          message: message,
          tree: tree.sha,
          parents: [state.headSha]
        }
      });

      try {
        await apiRequest(repoPath("/git/refs/heads/" + encodeURIComponent(branch)), {
          method: "PATCH",
          body: {
            sha: commit.sha,
            force: false
          }
        });
        return commit;
      } catch (error) {
        if (attempt === 0 && (error.status === 409 || error.status === 422)) continue;
        throw error;
      }
    }
    return null;
  }

  function enqueueWrite(operation) {
    var queued = writeQueue.then(operation, operation);
    writeQueue = queued.catch(function () {
      return undefined;
    });
    return queued;
  }

  function commitEntries(entries, message) {
    return enqueueWrite(async function () {
      var prepared = await prepareTreeEntries(entries);
      return commitPreparedEntries(prepared, message);
    });
  }

  async function loadDraft(editor) {
    requireReady();
    validateEditor(editor);
    var path = editor + "/current.json";
    var file = await apiRequest(repoPath("/contents/" + encodeRepositoryPath(path) + "?ref=" + encodeURIComponent(branch)), {
      allow404: true
    });
    if (!file) return null;

    var source;
    if (file.encoding === "base64" && file.content) {
      source = decodeBase64Text(file.content);
    } else {
      var raw = await downloadDraftFile(path);
      source = await raw.text();
    }
    return {
      data: JSON.parse(source)
    };
  }

  function saveDraft(editor, data, options) {
    requireReady();
    validateEditor(editor);
    options = options || {};
    var entries = [];

    (options.deletePaths || []).forEach(function (path) {
      entries.push({ path: validateDraftPath(editor, path), delete: true });
    });
    (options.files || []).forEach(function (file) {
      entries.push({
        path: validateDraftPath(editor, file.path),
        blob: file.blob
      });
    });
    entries.push({
      path: editor + "/current.json",
      content: JSON.stringify(data, null, 2) + "\n"
    });
    return commitEntries(entries, "Save " + editor + " draft");
  }

  function deleteDraft(editor, filePaths) {
    requireReady();
    validateEditor(editor);
    var entries = (filePaths || []).map(function (path) {
      return { path: validateDraftPath(editor, path), delete: true };
    });
    entries.push({ path: editor + "/current.json", delete: true });
    return commitEntries(entries, "Delete " + editor + " draft");
  }

  function downloadDraftFile(path) {
    requireReady();
    var editor = String(path || "").split("/")[0];
    validateEditor(editor);
    var safePath = validateDraftPath(editor, path);
    return apiRequest(repoPath("/contents/" + encodeRepositoryPath(safePath) + "?ref=" + encodeURIComponent(branch)), {
      raw: true,
      accept: "application/vnd.github.raw+json"
    });
  }

  function signOut() {
    clearStoredToken();
    token = "";
    ready = false;
    user = null;
    repository = null;
    window.location.reload();
  }

  async function initialize() {
    if (initialized) return;
    initialized = true;
    lock();
    if (!configured()) {
      showSetupRequired();
      return;
    }

    token = readStoredToken();
    if (!token) {
      showLogin();
      return;
    }

    showLoading();
    try {
      await verifyAccess();
      savePersistentToken(token);
      unlock();
      notifyReady();
    } catch (error) {
      clearStoredToken();
      token = "";
      showLogin(accessErrorMessage(error));
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
}());
