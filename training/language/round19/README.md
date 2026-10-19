# Round19 — 参考資料見出しによる既存TRAIN本文欠落の回復

Round18実10,000更新は最良NLL0.974257670、全文意味0/17で、前回最良0.973998407を更新できなかった。既存MAFF TRAINの参考資料見出しを含めて短い本文を捨てる単位化の欠落を修正する。既存6単位は保持し、参考資料より前の原文を元のchain定義で回復する。新規取得原文、Round18の追加原文は含めない。

Round16と同じRound11最新model・optimizer・RNGからの兄弟対照。8層192次元、独自語彙、40/30/30、ジャンル比、LR、seed系譜、開発検証、厳格な言語ゲートは固定。要求10,000更新と実counterを区別。公開モデルは変更しない。

実行: `bash training/language/round19/execution/run.sh`。未完了のみ`--resume`。稼働中・完了済みを二重実行しない。

実10,000更新を完了。最良NLLは追加step10,000の0.972624845998で、事前閾値0.973998407266を達成。全文意味0/17・初文7/17・非ループ4/17で厳格な言語ゲートは不合格。公開モデルは変更していない。[結果と原因分析](RESULTS.md)、[旧新の生成全文](execution/FULL_GENERATIONS.md)を参照。

訓練済み状態の再監査は `python training/language/round19/execution/verify_manifest.py`。保存済み全文の判定再現は `score_outputs.py` → `round10/review.py`（old/newそれぞれgeneration・manual・outを指定）→ `summarize.py`。これらは学習を再実行しない。教師強制の回復TRAIN診断は `measure_recovered_train.py`、結果報告は `build_report.py`。全成果を変更後に `freeze_results.py` → `verify_manifest.py` でSHAを再固定する。初期の自動保存にある意味判定pendingは当時の状態で、最終結果はRESULTS.mdとreview JSONを正とする。
