(function () {
  "use strict";

  var currentId = "";

  function identity(data, fallback) {
    if (data.draftId) return String(data.draftId);
    var slug = String(data.slug || "").trim().toLowerCase();
    if (slug) return "slug:" + slug;
    var title = String(data.title || "").trim().toLowerCase();
    if (title) return "title:" + title;
    return "commit:" + fallback;
  }

  window.NoteDraftIdentity = {
    identity: identity,
    get: function () {
      if (!currentId) currentId = "draft:" + window.crypto.randomUUID();
      return currentId;
    },
    open: function (data, fallback) {
      currentId = identity(data, fallback);
    },
    reset: function () { currentId = ""; }
  };
}());
