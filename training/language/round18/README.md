# Round18 — MAFF原文追加による少数データ枠の多様化

Round16と同じRound11最新の重み・optimizer・RNGから、追加の実10,000更新を行う兄弟対照。変更はMAFF TRAINに10文書・5867文字の原文を追加することのみ。ジャンル比、独自語彙、8層192次元、40/30/30、LR、検証、厳格な言語ゲートを保持。新規3文書1879文字はURL SHAで事前予約し訓練・評価に使わない。新TESTの主張はしない。

実行: `bash training/language/round18/execution/run.sh`。未完了のみ`--resume`。完了数はcheckpoint実counterで記録。公開モデルは変更しない。収集・整形・重複監査は`collect.py`と`sources/manifest.json`に記録。これは農業分野だけの小さな介入で、汎用的な現代日本語データ拡張とは扱わない。

実10,000更新完了。採用step9500、最良NLL0.974257670（前回最良0.973998407は未更新）、全文意味0/17。Python/JS17/17、厳格ゲート未達。詳細は[RESULTS.md](RESULTS.md)と無修正[全文](execution/FULL_GENERATIONS.md)。旧対照は同一rubricで再判定し、元判定も保持。
