(function () {
  "use strict";

  var status = document.getElementById("save-status");
  if (!status) return;

  function normalize() {
    var text = status.textContent || "";
    var replacements = [
      [/^GitHubに保存済み$/, "✓ GitHubに同期済み"],
      [/^端末内に保存済み$/, "✓ 端末に下書き保存済み"],
      [/^GitHubへの保存待ち…$/, "端末に保存済み・GitHubへ同期待ち…"],
      [/^GitHubに保存中…$/, "GitHubへ同期中…"],
      [/^保存中…$/, "下書きを保存中…"],
      [/^GitHubに接続済み$/, "✓ GitHubに接続済み"],
      [/^GitHubの下書きを復元しました$/, "✓ GitHubの下書きを復元しました"],
      [/^下書きを復元しました$/, "✓ 端末の下書きを復元しました"],
      [/^端末内に保存済み・GitHub未同期$/, "✓ 端末に保存済み・GitHub未同期"],
      [/^端末内の下書きを使用中・GitHub未同期$/, "✓ 端末の下書きを使用中・GitHub未同期"]
    ];
    for (var index = 0; index < replacements.length; index += 1) {
      if (replacements[index][0].test(text)) {
        var next = text.replace(replacements[index][0], replacements[index][1]);
        if (next !== text) status.textContent = next;
        return;
      }
    }
  }

  new MutationObserver(normalize).observe(status, { childList: true, characterData: true, subtree: true });
  normalize();
})();
