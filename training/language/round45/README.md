# R45 — 文脈CE係数0.1→0.2だけの比較

実10000更新完了。会話DEV NLLは微改善したが、selected日常全文0/12・従来0/17、terminal日常1/12・従来0/17。日常反復は旧より増え、厳格gate/固定実用条件/Paretoは未達で不採用。公開モデル/サイト/R25anchorは維持。

[結果・原因分析](RESULTS.md) / [旧新4状態168全文](execution/ALL_FOUR_STATE_GENERATIONS.md) / [再現](REPRODUCTION.md) / [次の一条件](NEXT_EXPERIMENT.md)。新84全文（83種類）を実際に読み、同一全文/初文と1k判定も照合。Py/JSとraw/exportは84全文一致、R10既知16/17は別記した。

0/200/1000/5000/selected9500/terminal10000のfull model/Adam/RNG・lossless parts・全SHA・loss CSVを保存。426入力は開始前commit5b82cd7で固定。初期read-only照合の作成待ちと接続側monitor再構築はあったが、trainer再起動/追加optimizer更新は0。

次は不採用係数を持ち越さずR44を科学対照に、LRだけ2倍の別ラウンドを提案。R45中は未訓練・実更新0。共有された不変データを将来編集する際は、先に独立コピーを作る。
