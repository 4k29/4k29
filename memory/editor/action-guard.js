(function () {
  "use strict";

  var form = document.getElementById("memory-form");
  var status = document.getElementById("save-status");
  var buttons = [
    document.getElementById("save-draft-button"),
    document.getElementById("publish-button")
  ].filter(Boolean);

  if (!form || !buttons.length) return;

  buttons.forEach(function (button) {
    button.addEventListener("click", function (event) {
      if (button.dataset.memoryActionReady === "true") {
        delete button.dataset.memoryActionReady;
        return;
      }

      if (/軽量化中/.test(status.textContent || "")) {
        event.preventDefault();
        event.stopImmediatePropagation();
        window.alert("写真の軽量化が終わってから操作してください。");
        return;
      }

      event.preventDefault();
      event.stopImmediatePropagation();
      button.disabled = true;
      status.textContent = "最新の内容を準備中…";
      form.dispatchEvent(new Event("input", { bubbles: true }));

      window.setTimeout(function () {
        button.disabled = false;
        button.dataset.memoryActionReady = "true";
        button.click();
      }, 900);
    }, true);
  });
}());
