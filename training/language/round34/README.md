# Round34 — 実10000更新と全文評価完了

人間の発話末尾へ自己負例prefixを合わせる1条件を検証した。R33と同じR28 full model/Adam20000/RNGから同じ10000更新、独自8層×192、BPE40/30/30、同一データ・LR・seed。選択8000と終了10000の新全文84件を実際に読んだが、日常会話の意味成立は各診断とも0で、改善は実証できず標準採用なし。研究anchorR25と公開モデルは維持する。

[結果と原因分析](RESULTS.md) / [再現・checkpoint復元](REPRODUCTION.md) / [旧新4状態168出力の全文](execution/ALL_FOUR_STATE_GENERATIONS.md) / [実更新・最終評価](execution/final-assessment.json) / [採否](execution/adoption-decision.json)。全て露出DEVで新TESTではない。従来の厳格ゲートとselectorは変更していない。

source5の比較元allowlistが古く評価のみ一度失敗した。凍結コードと失敗ログを残し、別wrapperで指定だけ修復して全件測定した。学習の再実行や出力修正はない。詳細はexecution/fixed-source-allowlist-recovery.json。初期条件・データ・コードの367SHAは学習後も一致し、最新・選択・zeroと途中200/1000/5000のfull stateをlossless partsで保持する。自動保存時のpending記録は、その時点の履歴でありfinal-assessmentが最終状態を示す。
