# R44の復元と照合

commit32989336871deb15a3778076eed6b8b9a7b8d2b7で426入力を実更新0時点に凍結。source-manifest.jsonとpolicy.jsonにデータ/コード/初期state SHA、execution/launch.jsonにUTCと起動command、execution/run.shに固定CLIを保存。外部raw cacheは/workspace/daily-conversation-source-audit/human-only-raw、資料の取得commit/利用条件/話者splitはprospective-daily-sourceと既存R28 source manifestで固定。新たなTESTや別モデルを使わない。

保存結果の確認はリポジトリrootから次を実行する。

```bash
python training/language/round44/execution/verify_final_artifacts.py --require-tracked
```

raw checkpointやtrain.tokens.binがなければ、隣接*.chunks.jsonと全partのSHAを確認してlossless復元する。初期0、実200/1000/5000、selected9500/Adam29500、latest10000/Adam30000の6 fullstatesを保持。selected-weights.ptは推論用、optimizer/RNGの再開はfullstateを使う。selected重みをlatest optimizerへ混ぜない。

全10000更新は完了済み。既存runを再訓練しない。再現学習が必要な場合は別clone/別出力で成果を保護し、入力426SHA、初期R28 full model/Adam20000/RNG、初期DEV一致を先に確認して、execution/run.shのCLIを使用する。policy/seed/LR/selector/threads/FP32を変えない。物理更新を予定値から推定せず、実checkpoint step・Adamcounter・traceで照合する。

元pipeline.shはpost-training diagnose_parity.mjsのコピー漏れでexit1となった履歴を持つ。追加したmjsはR43とbytes同一、元426frozen入力は変更しない。今回の評価回復にはexecution/resume_posttraining_evaluation.sh（失敗点以降のみ）とrecover_terminal_after_primary.pyを使った。posttraining-evaluation-recovery.json、terminal-recovery-status.json、evaluation-recovery-complete.jsonに証拠を保存。学習の再実行は0。

結果を再計算する際は既存のgeneration/readingを不用意に上書きせず別出力にする。reading-notes-as-executed.jsonとrecord_final_readings_as_executed.pyは、今回実際に読んだ生成SHA専用の履歴binderであり、将来出力の自動意味graderではない。同一全文/初文の判定照合はconfirm_all_new_readings.py/verify_first_sentence_consistency.py、全168全文の組立はassemble_raw_four_states.py、数値範囲はverify_final_numerics.pyで確認する。既知R10 16/17分岐を保持。

CSVはinstantaneous-training-loss-curve.csv、context-auxiliary-curve.csv、paired-ce-curve.csv。前二者は1 minibatch/aux2組の標本損失で全TRAIN平均ではない。人間TRAIN99とDEV99は長さ/話題がmatchedでなく、TRAIN64の7/57も両方TRAIN。全source/token監査と意味の全件監査は区別する。

ローカルsparse working treeの93旧preparedファイル除外はGit履歴削除ではない。復元前の容量確認と手順はWORKSPACE_STORAGE.md。Git自動gcはローカルで無効化し、モデルの一意なstateや履歴は削除していない。
