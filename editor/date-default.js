(function () {
  "use strict";

  var dateField = document.getElementById("date");
  var dateDisplayField = document.getElementById("date-display");

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
