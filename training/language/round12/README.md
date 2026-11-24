# Round 12 — 文字境界ビューの一因子対照

Round 11の全文意味0/17を受け、TRAIN混合のみ通常/Glyph/文字境界=70/30/0へ変更する。Round 11と同じRound 10親重み、原文、独自語彙、seed2049、FP32、8層dim192、context256、fresh AdamW、LR/warmup/cosine、batch8、CPU2、10,000更新を固定。選択は共通3ビュー40/30/30の開発NLL/UTF8 byte。追加更新による継続ではなく、前回推奨した文字境界分割の効果を分離する対照。Round 11のデータを読み取り専用で再利用し、原文やtoken streamを再作成しない。

訓練: `bash training/language/round12/execution/run.sh`。既存checkpointがある場合は同じcommandに`--resume`を追加する。採用重みと最新optimizerを混ぜない。TEST生成、公開モデル交換、instruction tuningは禁止。実行数と合否はRESULTS.mdに実測だけを記録する。

実行結果: **10,000更新完了、全文意味0/17、言語ゲート不合格**。[RESULTS.md](RESULTS.md)と[全文比較](execution/FULL_GENERATIONS.md)を参照。共通開発lossはRound 11より悪化し、この混合比を公開モデルに採用していない。
