# Round41 — correct-context CE only、実10000更新完了・不採用

同じR28 full model/Adam20000/RNGから、R40の補助pairwise softplusをcorrect-context CEへ変更する一条件比較を実行した。mainデータ・BPE40/30/30・source25/5・モデル・LR・seed・既存目的・256組/係数/順序・10000dose・selector・全ゲートは固定。補助canonical追加露出は別計数。不一致文脈は診断のみで勾配に寄与しない。

実10000更新、Adam30000、選択9000/Adam29000。人間会話DEV99 NLL0.93459819→0.93383869と改善したが、日常全文意味0/12→0/12、原文native最小行為3→2、source最小行為1→0。原17初文6→7・非loop2→3の部分的改善も、全文意味0と全厳格gate未達を覆さず、不採用。公開モデル・サイト・研究anchor R25を維持。

新84全文を実際に読み、77異なるprefix/fulltext対と重複判定の整合を確認。旧新selected/terminal全168全文と実token列を保存。新84/84 Py/JS、84/84 raw FP32/export全文一致、既知R10 near-tieは保持。評価は露出済DEVで新TESTではない。

- [結果・失敗分析・判定境界](RESULTS.md)
- [全168生成全文](execution/ALL_FOUR_STATE_GENERATIONS.md)
- [再現・復元・完了guard](REPRODUCTION.md)
- [実判定](execution/final-assessment.json)
- [次の一条件候補（未実装・未訓練）](NEXT_EXPERIMENT.md)
