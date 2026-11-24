# Round21 — UL係数0.1→0.3の単独対照

Round20の実10,000更新では非ループ4→6/17、生成4-gram重複率55.6→53.4%だが全文意味0/17、通常CEの最良NLLは前回最良を更新しなかった。係数だけを0.1から0.3へ変更し、反復低下の効果と必要な反復・文法・CEへの副作用を調べる。

Round20と同じ回復済みデータ全byte・fold・独自語彙・8層192次元・40/30/30・ジャンル比・seed系譜2049・batch8・CPU2 FP32・一定LR2.2499999999999998e-5を維持。UL履歴64、非特殊tokenの一意候補、gold除外、mask、確率上限1-1e-6、正解targetsは不変。CE+0.3ULで学習し、通常CEだけの固定DEV NLLで採用checkpointを選ぶ。生成時の反復penaltyは使わない。

Round20と同じRound11最新model/AdamW/Torch/private Python RNGからの兄弟対照で、Round20最終から更新を延長する実験ではない。追加10,000更新、検証500ごと。事前NLL進捗閾値は全ラウンド最良0.972624845997683のまま。初文80%・非ループ90%・全文意味80%の全scope/groupのゲートを維持する。既存17件は露出済みDEVで、新TESTではない。公開モデル・サイト・TEST生成を変更しない。原文とライセンスはRound19の不変成果にSHAで結合する。

実行 `bash training/language/round21/execution/run.sh`。未完了だけ`--resume`、稼働中・完了済みを重複実行しない。persistent.shが学習・機械比較・実counter/重み/optimizer/RNGのPR保存をチャットから独立して行う。意味判定は全出力読解後にのみ追加する。準備時点の実験更新0を完了扱いしない。

実10,000更新を完了し、最良は追加step10,000のNLL0.973161003725。Round20の0.972678965659より悪化し、全ラウンド最良の進捗閾値も未達。初文8/17・非ループ6/17・全文意味0/17で、全言語ゲート不合格。通常CEは学習後の全20検証時点で対照より高く、重複4-gram率も53.4→56.4%へ悪化した。[結果と原因分析](RESULTS.md)、[生成全文](execution/FULL_GENERATIONS.md)を参照。

保存状態の再監査は`python training/language/round21/execution/verify_manifest.py`。保存済み全文の判定再現は`score_outputs.py`→`round10/review.py`（old/newそれぞれgeneration・manual・outを指定）→`summarize.py`。`compare_losses.py`でCE/ULと全検証時点の学習量、`verify_paired_exposure.py`で対照との最終RNG/exposure一致を確認する。`measure_repetition.py`は事後診断でゲートを代替しない。`measure_recovered_train.py`はTRAIN教師強制診断。`build_report.py`で結果報告を作成し、成果変更後は`freeze_results.py`→`verify_manifest.py`でSHAを再固定する。学習を再実行する必要はない。自動保存のpendingは当時のsnapshotで、最終判定はRESULTS.md/review JSONを参照。
