# Inherited Adam LR sensitivity

Draft PR110。新規条件は MIX-579 を継承し、PR109と同一の追加401batch/409,856targetsをLR3e-5で一巡。比較LR1e-5は既存保存結果を再利用。

- [REPORT.md](REPORT.md): 実結果、失敗、限界、No-Go
- [TABLES.md](TABLES.md): source別予測・境界・caption全32件
- [PLAN.json](PLAN.json), [CONDITION_MATCH_AUDIT.json](CONDITION_MATCH_AUDIT.json): 更新前固定と一致監査
- [UPDATES.jsonl](UPDATES.jsonl): 実呼出し405、保持401
- [CHECKPOINT_INDEX.json](CHECKPOINT_INDEX.json): 全状態3保存点のSHA/cold復元commit
- evaluation/: 無修正greedy全文/token/raw bytes、40境界top10/確率/teacher-forced比較
- ADJUDICATION-*.json: main assistant非盲検の全129必須入力の読解判定。独立人間評価ではない。
- [NEXT_STRATEGY.md](NEXT_STRATEGY.md): 次の研究1案（未実行）

既存PLANは凍結済み。学習run42921736667は完了済みなので再起動しない。run.pyはrerun/進行状態不整合を拒否する。復元はCHECKPOINT_INDEXの固定Git commitをfresh remote-only bare repositoryへfetchし、verify_pinned.py --repository <bare> --cursors 4 205 401で照合する。restore_checkpoint.pyの引数は --help、同一chunk順序とSHAを確認する。学習済みstateは公開モデルとして採用しない。

読解後の再集計（optimizer0/forward0）:

```sh
python training/language/conversation-v2/lr-sensitivity-study/summarize_results.py
python -m unittest discover -s training/language/conversation-v2/lr-sensitivity-study -p test_results.py
```

sourceの利用条件/帰属/加工記録は元コーパスと既存台帳を継承し、新しい権利を付与しない。新規コーパス取得なし。封印TEST未使用、公開モデル/サイト変更なし、マージなし。
