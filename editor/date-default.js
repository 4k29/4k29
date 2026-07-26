(function () {
  "use strict";

  var dateField = document.getElementById("date");
  var dateDisplayField = document.getElementById("date-display");
  var memoryForm = document.getElementById("memory-form");
  var titleField = document.getElementById("title");
  var descriptionField = document.getElementById("description");
  var descriptionCount = document.getElementById("description-count");
  var automaticDescription = "";

  if (!dateField) return;

  function jstDate() {
    var parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Tokyo",
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    }).formatToParts(new Date());
    var values = {};

    parts.forEach(function (part) {
      values[part.type] = part.value;
    });

    return values.year + "-" + values.month + "-" + values.day;
  }

  function halfWidthHyphens(value) {
    return String(value || "").replace(/[‐‑‒–—−]/g, "-");
  }

  function memoryDescription(dateDisplay, title) {
    return dateDisplay && title ? dateDisplay + " - " + title : "";
  }

  function updateMemoryDescription(event) {
    if (!memoryForm || !dateDisplayField || !titleField || !descriptionField) return;

    var rawDateDisplay = dateDisplayField.value.trim();
    var normalizedDateDisplay = halfWidthHyphens(rawDateDisplay);
    var title = titleField.value.trim();
    var currentDescription = descriptionField.value.trim();
    var nextDescription = memoryDescription(normalizedDateDisplay, title);
    var legacyDescription = rawDateDisplay && title
      ? rawDateDisplay + " — " + title + "で撮影した写真の記録。"
      : "";
    var legacyShortDescription = rawDateDisplay && title
      ? rawDateDisplay + " — " + title
      : "";

    if (rawDateDisplay !== normalizedDateDisplay) {
      dateDisplayField.value = normalizedDateDisplay;
    }

    if (event && event.target === descriptionField) {
      automaticDescription = "";
      return;
    }

    if (
      !currentDescription ||
      currentDescription === automaticDescription ||
      currentDescription === legacyDescription ||
      currentDescription === legacyShortDescription
    ) {
      descriptionField.value = nextDescription;
      automaticDescription = nextDescription;
      if (descriptionCount) descriptionCount.textContent = nextDescription.length;
    }
  }

  function prepareMemoryPlaceholders() {
    if (!memoryForm || !dateDisplayField || !descriptionField) return;
    dateDisplayField.placeholder = "2026.07.22-24";
    descriptionField.placeholder = "2026.07.22-24 - Tokyo";
    updateMemoryDescription();
  }

  function ensureDate() {
    var changed = false;

    if (!dateField.value) {
      dateField.value = jstDate();
      changed = true;
    }

    if (dateDisplayField && !dateDisplayField.value) {
      dateDisplayField.value = dateField.value.replace(/-/g, ".");
      changed = true;
    }

    if (changed) {
      dateField.dispatchEvent(new Event("input", { bubbles: true }));
    }

    updateMemoryDescription();
  }

  if (memoryForm) {
    memoryForm.addEventListener("input", updateMemoryDescription);
    prepareMemoryPlaceholders();
  }

  [0, 250, 1000, 3000, 8000].forEach(function (delay) {
    window.setTimeout(ensureDate, delay);
  });

  window.addEventListener("pageshow", ensureDate);
  window.addEventListener("focus", ensureDate);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") ensureDate();
  });
}());