# LF boundary study（Draft PR #107）

結果は[REPORT.md](REPORT.md)、40境界は[TABLES.md](TABLES.md)、補助交差評価は[CROSS_TABLES.md](CROSS_TABLES.md)。正式採用なし。元のPR #106ファイルは変更しない。

- `PLAN.json`：更新前の条件・SHA。`build.py`は凍結済みPLANがあれば停止する。
- `corpus-LF1.json.gz`／`schedule-LF1.json.gz`：LF1研究表現と元と同じ順序の579バッチ。
- `POSITION_MAP.json.gz`／`BYTE_MAP.json.gz`：全内容の原文との対応。原文は既存paragraph-foundation/corpus.jsonl.gz。
- `TRANSFORM_AUDIT`／`TEACHER_MASK_AUDIT`／`POSITION_SHIFT_AUDIT`：境界・教師・padding・位置変化。
- `UPDATES.jsonl`：actual intent/completed（579保持＋4検証）。予定更新数と区別する。
- `artifacts/LF1-{4,289,579}`：完全状態のlossless分割とSHA。Git-only取得証拠は`GIT_RESTORE-*.json`。
- `evaluation/*-LF1.json`：149固定単発入力と自己履歴、無修正全文・token列・raw bytes・停止理由。`*-boundaries.json`は40境界、32組C/U、本文8tokensの確率・順位・上位10候補。
- `*_READING.json`：main assistantの全文読解。`SCREEN`は強い必要条件違反、`REVIEW_CARDS`はそれ以外の全文。独立人間評価ではない。
- `CONTROL_REUSE`／`*_REUSE_AUDIT`：旧生成・旧読解を再利用した根拠。
- `parity-terminal`：12位置の限定数値照合。失敗したNode初回起動logも保持。

## 学習を行わない検証

リポジトリrootから：

```sh
python -m unittest discover -s training/language/conversation-v2/lf-boundary-study -p test_transform.py
python training/language/conversation-v2/lf-boundary-study/ci_audit.py
python training/language/conversation-v2/lf-boundary-study/audit.py
python training/language/conversation-v2/lf-boundary-study/summarize.py
```

`audit.py`は元の凍結コーパスも照合する。`summarize.py`は保存結果のみを集計し、モデルを呼ばない。専用CIはweights・大量評価結果をcheckoutせず、4テストと凍結LF1入力監査のみを行う。

## Git-only checkpoint復元

4.9GiB級のscratchとRAM8GiBを持つ隔離checkoutを推奨する。永続overlay約300MiBでは安全なstate復元を開始しない。例：

```sh
python training/language/conversation-v2/lf-boundary-study/restore_git.py --model initial --destination scratch/initial.pt
python training/language/conversation-v2/lf-boundary-study/restore_git.py --model control-LF2 --destination scratch/LF2-terminal.pt
python training/language/conversation-v2/lf-boundary-study/restore_git.py --model LF1-579 --destination scratch/LF1-579.pt
python training/language/conversation-v2/lf-boundary-study/verify.py
```

復元はGit blobsだけを使い、各chunk・whole SHAを照合してからatomic renameする。既存ファイル／pendingは上書きしない。`verify.py`は保存された全状態とledger・出力byte・呼出し数を照合し、モデルforward・optimizerを実行しない。

学習を再現する場合は**別のrun ID・隔離checkout**を使い、freeze commit `87f758b`の条件を保持する。既存の完了済みledgerを新runの実呼出しとして流用しない。初期全状態を復元し、独立ledgerで0→4→289→579の固定段階を実行する。既存状態からの継続は`resume_guard.py --until ...`を使い、checkpointと実ledgerの一致を先に確認する。ledgerがcheckpointより先にある場合は自動replayせず、実呼出し・回復replayを明示的に監査する。本研究は579更新で完了しており、このbranchから追加epochを起動しない。

既存保存済み評価を上書きしない。初期／中間／終端の自由生成は既に完了しているため、報告を読むだけの場合に再推論する必要はない。
