# Round20 — causal token unlikelihood の単独対照

Round19は実10,000更新でDEV NLL0.972624845998を達成したが、全文意味0/17、長い反復13/17。教師強制の局所改善が自由生成へつながらない問題に対し、訓練目的だけを変更する。

CE + 0.1 × UL。UL候補は各入力位置までの直前64tokenの一意な非特殊token（ID>=6）から正解の次tokenを除外。各候補の-log(1-p)を合計し有効target数で平均する。pは最大1-1e-6に固定。maskされたtarget位置は対象外。将来の入力tokenは参照しない。通常のCE targetsを変更せず、生成文・他モデルの文章を教師に使わない。正しい反復や機能語を損なう可能性を含め評価する。

Round19と同一の回復済みTRAIN・fold・ライセンス・独自語彙・8層192次元・40/30/30・ジャンル比・batch8・CPU2 FP32・一定LR2.2499999999999998e-5を保持。Round19と同じRound11最新のmodel/AdamW/Torch/private Python RNGからの兄弟対照で、Round19最終からさらに10,000更新する実験とは区別する。データと乱数消費を固定して目的の効果を分離する。

要求は追加10,000更新、検証500更新ごと。通常のCE NLLで採用checkpointを選び、ULを検証指標へ混ぜない。新しいNLL進捗閾値はRound19最良0.972624845997683。従来の厳格な全文言語ゲートは変更しない。同じ17件は露出済みDEVでTESTではない。公開モデル・Web挙動は変更しない。

実行: `bash training/language/round20/execution/run.sh`。中断した未完了状態だけ`--resume`で同一条件再開し、稼働中・完了済みを二重実行しない。独立したpersistent.shが学習→機械比較→実counterと重みのPR保存を行う。意味評価は全文読解後のみ追加する。準備時点では実験optimizer更新0、完了とは扱わない。

実10,000更新を完了し、最良は追加step10,000のNLL0.972678965659。Round19の0.972624845998を更新せず、事前進捗条件は未達。初文7/17・非ループ6/17・全文意味0/17、全言語ゲート不合格。通常CE・反復抑制損失を別記録し、対照と実exposure・最終RNGが完全一致することを確認した。[結果と原因分析](RESULTS.md)、[旧新の生成全文](execution/FULL_GENERATIONS.md)を参照。

保存済み状態の再監査は `python training/language/round20/execution/verify_manifest.py`。意味判定の再現は `score_outputs.py`、`round10/review.py`（old/newそれぞれgeneration・manual・outを指定）、`summarize.py`。`compare_losses.py`で合成目的とCE/UL、各検証時点の実exposureを確認する。`measure_repetition.py`は生成部分だけの事後診断でゲートを代替しない。`measure_recovered_train.py`はTRAINの教師強制診断。最終報告は`build_report.py`、成果変更後のSHA再固定は`freeze_results.py`→`verify_manifest.py`。いずれも学習を再実行しない。自動保存のpendingは当時のsnapshotで、最終判定はRESULTS.mdとreview JSONを参照。
