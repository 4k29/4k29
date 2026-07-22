(function () {
  "use strict";

  var TOKEN_KEYS = [
    "4k29-editor-github-token-persistent",
    "4k29-editor-github-token"
  ];
  var API_ROOT = "https://api.github.com";
  var OWNER = "4k29";
  var REPOSITORY = "4k29";
  var BRANCH = "main";
  var IMAGE_DIRECTORY = "images/notes";

  var uploadButton = document.getElementById("image-upload-button");
  var uploadInput = document.getElementById("image-upload-input");
  var uploadStatus = document.getElementById("image-upload-status");
  var imagePathInput = document.getElementById("dialog-image-path");
  var imageAltInput = document.getElementById("dialog-image-alt");
  var imageDialog = document.getElementById("image-dialog");
  var body = document.getElementById("body");

  if (!uploadButton || !uploadInput || !uploadStatus) return;

  function readToken() {
    try {
      return window.localStorage.getItem(TOKEN_KEYS[0]) || window.sessionStorage.getItem(TOKEN_KEYS[1]) || "";
    } catch (error) {
      return "";
    }
  }

  function safeFileName(name) {
    var dot = name.lastIndexOf(".");
    var extension = dot >= 0 ? name.slice(dot).toLowerCase() : "";
    var base = dot >= 0 ? name.slice(0, dot) : name;
    base = base
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^A-Za-z0-9_-]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .toLowerCase();
    if (!base) base = "image";
    return base + "-" + Date.now() + extension;
  }

  function blobToBase64(file) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onerror = function () {
        reject(reader.error || new Error("画像を読み込めませんでした"));
      };
      reader.onload = function () {
        resolve(String(reader.result).split(",")[1] || "");
      };
      reader.readAsDataURL(file);
    });
  }

  async function uploadFile(file) {
    var token = readToken();
    if (!token) throw new Error("GitHubキーが見つかりません");

    var filename = safeFileName(file.name);
    var path = IMAGE_DIRECTORY + "/" + filename;
    var content = await blobToBase64(file);
    var response = await window.fetch(
      API_ROOT + "/repos/" + OWNER + "/" + REPOSITORY + "/contents/" + path.split("/").map(encodeURIComponent).join("/"),
      {
        method: "PUT",
        headers: {
          "Accept": "application/vnd.github+json",
          "Authorization": "Bearer " + token,
          "Content-Type": "application/json",
          "X-GitHub-Api-Version": "2022-11-28"
        },
        body: JSON.stringify({
          message: "Upload note image: " + filename,
          content: content,
          branch: BRANCH
        }),
        cache: "no-store",
        credentials: "omit"
      }
    );

    if (!response.ok) {
      var details = null;
      try {
        details = await response.json();
      } catch (error) {
        details = null;
      }
      var uploadError = new Error(details && details.message ? details.message : "GitHubへアップロードできませんでした");
      uploadError.status = response.status;
      throw uploadError;
    }

    return {
      markdownPath: "../" + path,
      ogpPath: "/" + path,
      filename: filename
    };
  }

  function insertImageMarkdown(path, alt) {
    var start = body.selectionStart;
    var end = body.selectionEnd;
    var markdown = "![" + alt.replace(/\]/g, "") + "](" + path.replace(/\s/g, "%20") + ")";
    var before = body.value.slice(0, start);
    var after = body.value.slice(end);
    var prefix = before && !/\n\n$/.test(before) ? "\n\n" : "";
    var suffix = after && !/^\n\n/.test(after) ? "\n\n" : "";
    body.value = before + prefix + markdown + suffix + after;
    var caret = (before + prefix + markdown).length;
    body.setSelectionRange(caret, caret);
    body.dispatchEvent(new Event("input", { bubbles: true }));
    body.focus();
  }

  uploadButton.addEventListener("click", function () {
    uploadInput.click();
  });

  uploadInput.addEventListener("change", async function () {
    var file = uploadInput.files && uploadInput.files[0];
    if (!file) return;

    if (!/^image\/(jpeg|png|webp|gif|avif)$/i.test(file.type)) {
      window.alert("JPEG、PNG、WebP、GIF、AVIFの画像を選んでください。");
      uploadInput.value = "";
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      window.alert("画像は20MB以下にしてください。");
      uploadInput.value = "";
      return;
    }

    uploadButton.disabled = true;
    uploadStatus.textContent = "GitHubへアップロード中…";

    try {
      var uploaded = await uploadFile(file);
      var suggestedAlt = file.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ");
      imagePathInput.value = uploaded.markdownPath;
      imageAltInput.value = suggestedAlt;
      uploadStatus.textContent = "アップロード済み：" + uploaded.filename;
      insertImageMarkdown(uploaded.markdownPath, suggestedAlt);
      if (imageDialog && imageDialog.open) imageDialog.close();
    } catch (error) {
      if (error.status === 403 || error.status === 404) {
        uploadStatus.textContent = "4k29リポジトリへの書き込み権限がありません";
        window.alert("GitHubキーの対象リポジトリに「4k29」を追加し、ContentsをRead and writeにしてください。");
      } else {
        uploadStatus.textContent = "画像をアップロードできませんでした";
        window.alert("画像をアップロードできませんでした。通信状況を確認してください。");
      }
    } finally {
      uploadButton.disabled = false;
      uploadInput.value = "";
    }
  });
})();
