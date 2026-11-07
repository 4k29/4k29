# Round 16 — optimizerとRNGを保持した追加学習

Round 11最新step10000の重み・AdamW moment・Torch/Python RNGから追加10,000更新。採用step9500のbeststateと最新optimizerを混ぜない。ジャンル45/10/10/15/10/2.5/5/2.5%、通常/Glyph/文字境界40/30/30、8層dim192、独自語彙・原文・fold・context256を保持。既存cosineの終端値を追加区間で固定する拡張規則を事前に定義し、warmup・optimizer・RNGを再初期化しない。

Round 11で7000→9500のNLLが改善を続けていたことを追加学習の根拠にした。語彙・モデル容量・データの多様性を増やした実験ではない。共通開発NLLが0.9788898793272423を下回る、または既存の厳格な言語ゲートを合格することが今回の進捗目標。NLLのみの改善を日本語能力の改善とは呼ばない。TEST生成・公開モデル交換は禁止。

新規実行: `bash training/language/round16/execution/run.sh`。未完了のcheckpointからだけ、同commandに`--resume`を付ける。完了済み実験は再開せず、audit/verify_manifestで確認する。実更新数とoptimizer counterには親の10000更新との差があるため、RESULTS.mdで区別する。
