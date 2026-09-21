(function () {
  "use strict";

  var form = document.getElementById("memory-form");
  var buttons = [
    document.getElementById("save-draft-button"),
    document.getElementById("publish-button")
  ].filter(Boolean);

  if (!form || !buttons.length) return;

  buttons.forEach(function (button) {
    button.addEventListener("click", function (event) {
      if (window.MemoryEditor && window.MemoryEditor.isProcessing()) {
        event.preventDefault();
        event.stopImmediatePropagation();
        window.alert("写真の軽量化が終わってから操作してください。");
        return;
      }

    }, true);
  });
}());
