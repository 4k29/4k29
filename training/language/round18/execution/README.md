# 実行記録

`launch.json`に記録した独立プロセスが実学習と機械評価を実行する。チャット接続とプロセスの生存は別。`progress.py`はログ上の最後の更新とプロセス状態を表示し、未完了を完了扱いしない。100更新ごとのcheckpointにはモデル、AdamW、Torch/Python RNG、実counterを保存する。予防的な中断は行わない。

未完了の同一条件再開: `bash training/language/round18/execution/run.sh --resume`。実行中プロセスとcheckpoint counterを先に確認し、二重起動・完了済み再実行は禁止。

`verify_addition.py`は追加30viewを原文から独立にバイト検証し、mask対象の一回被覆・予約原文の除外を検査。`check_sampling.py`は固定ジャンル・view確率、`verify_runtime.py`は全パラメータ勾配とparent optimizer/RNG、`verify_initial.py`は実step0 snapshotとの完全一致を検査する。

`pipeline.sh`は実10,000更新の後にcounter・初期状態・sampler replay・同一17入力での全文生成・Python/JS一致・丸め誤差・数値分岐・生成粒度・固定TRAIN/DEV loss差を記録する。手動全文読解は機械評価完了後に行い、生成SHAへ判定を拘束する。合格基準や文章を後から変更しない。
