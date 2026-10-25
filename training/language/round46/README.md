# R46 — 学習率だけ2倍、実10,000更新完了

R44対照、LR0.0000225→0.000045のみ。selected9500の会話DEV NLL/byteは0.917695→0.908436、人間会話8件の全文成立は2→4。ただしselected17全文0、日常12全文0/loop4、共通DEV悪化。terminal17全文は1→3で、従来全gate・採用条件は不合格。正式採用false、公開/R25anchor維持。全84実読解・168全文・6fullstatesを保存。

後処理のLRログ検査不備で元pipelineはexit1。430入力/訓練済み重みを変えず評価だけ復旧し、全84PyJS/raw-export一致を確認した。RESULTS.md/REPRODUCTION.mdとposttraining-recovery.jsonを参照。新TESTや独立盲検人手評価ではない。
