# 返答単位focusと実比較

[結果](REPORT.md) / [実更新数](SUMMARY.json) / [無修正生成全文](evaluation14/GENERATIONS.md) / [実行前条件](PLAN14.json) / [初回不備と破棄記録](invalid-trial-incident.json)

共通medium3470からA/B各14保持更新を実施し、7→14の全状態・traceの再計算一致を確認した。総実optimizer.step84=保持28+正常replay14+初回無効42。旧23と内容24の成功はともに0。大きい211更新の候補scheduleは未認可・未実行。正式モデル採用、公開変更、マージ、有料資源使用なし。

checkpointはexecution14/{control,treatment}/archive/checkpoint.jsonと32MiB以下の全chunk。完全model・Adam・Torch/private RNG・旧sampler provenance・allocation_cursor・全traceを保持する。共通初期状態のrestoreにはdeepcopyが必須。旧PR98の禁止gateを解除しない。

オフライン検証（repository root）:

```sh
python training/language/conversation-v2/reply-focus/verify.py
python -m unittest discover -s training/language/conversation-v2/reply-focus -p 'test_*.py' -v
```

execute14.pyは実際に更新する研究用コードであり、検証コマンドとして再実行しない。既存endpointへの上書きは禁止し、再実行には新しい保存領域・計画・global実更新ledgerが必要。childモードは保存済み7更新snapshot専用。現在その一時snapshotは試験後に削除済みで、成功endpointを上書きして再開する仕様ではない。実行時のコード・計画・traceはGit履歴とSHAで再現できる。通常CIは更新せず保存済み結果の契約とSHAだけを検証する。

データは既存RP TRAINのsource SHA/IDで参照し、源のCC BY-SA4の帰属・利用条件はconversation-v2/DATA_STRATEGY.mdを継承する。新たに元会話本文や隔離された個人情報を転載しない。新規の外部学習済みモデル/Tokenizer/生成APIは不使用。評価は露出済みDEVの診断であり、独立人間評価や封印TESTではない。

実行後にdriverへ既存receipt/archiveの再実行拒否を追加した。実際に学習した原codeはEXECUTED_RUNNER.pyとcommit326bd40、PLAN14.jsonのrunner_sha256がそれを指す。現在driverを旧planへそのまま再実行する用途はない。再現は記録commitの新しいcheckout/保存先で行い、累積実更新数を別途記録する。
