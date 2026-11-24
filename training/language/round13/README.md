# Round 13 — 既存原文のジャンル構成対照

同じRound 10採用親重みから実10,000更新を行う。通常/Glyph/文字境界40/30/30、8層dim192、語彙、原文/fold、seed2049、FP32、CPU2、fresh AdamW、LR/schedule/batch/context、共通開発選択、全文ゲートはRound 11と共通。Aozora比率のみ45%から35%へ減らし、差分をMDN以外の既存現代説明文へ元比率に比例配分。MDN15%は固定。新規原文の追加・独立した3因子の変更・最新重みへの単純継続ではない。実原文の多様性を増やしたとは主張しない。

`policy.json`のgenreSamplingが事前固定条件。Round 11 preparedデータを読み取り専用で再利用する。訓練command: `bash training/language/round13/execution/run.sh`。checkpointがある場合は同じcommandに`--resume`を付ける。実完了数・合否はRESULTS.mdに記録する。TEST生成、instruction tuning、公開モデル交換は禁止。
