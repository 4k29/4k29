# Round40 — 人間文脈の相対尤度を学ぶ補助目的

**実10,000更新を完了、不採用。** 日常12件の全文意味成立は旧新とも0。補助集合の文脈gapは改善したが、別のTRAIN診断組の正しい文脈NLLは悪化した。限定的な反復減少・短い相槌は、内容のある会話の改善を示さなかった。研究anchor R25、公開モデル・サイトは変更していない。

R39と同じR28 latestのmodel/Adam20000/RNGから開始した兄弟比較。唯一の学習変更は、元の人間TRAIN256組の正しい文脈と同長の別文脈に対し、同じgold次発話の平均token NLL差をsoftplusで学ぶ補助目的（0.1/every10/batch2）。他モデルの生成や外部の学習済み重み/tokenizer/APIは使わない。mainのデータ・source25%/5%・独自BPE40/30/30・8層192・LR・seed・既存損失・selector・推論・全gateを維持。追加canonical補助露出はmainと別に記録する。

[結果・原因分析](RESULTS.md)、[旧新4状態168出力の無加工全文](execution/ALL_FOUR_STATE_GENERATIONS.md)、[再現手順](REPRODUCTION.md)、[次の単一条件候補・未実行](NEXT_EXPERIMENT.md)。新しい84状態出力は全文を読解し、79の異なるprefix/全文組に整理した。同文面・同初文の採点一致を確認。全て露出済み開発診断で新TESTではない。
