# Round41 — correct-context CE only

**実1000更新の中間検証まで保存済み。学習は10000更新へ継続中で、最終結果・採用判定は未完了。** 科学対照R40、参考R39。同じR28 full model/Adam20000/RNGからの兄弟比較であり、R40terminalの延長ではない。

唯一の変更は、同じ元の人間TRAIN256組による補助損失を`softplus(correctNll - wrongNll).mean()`から`correctNll.mean()`にすること。wrong forwardは診断だけに残し、損失・勾配に寄与しないことをテストした。モデル、独自BPE、main40/30/30、source25/5、全mainデータ、補助pool/係数0.1/every10/batch2/順序、LR、seed、10000dose、既存全目的、DEV selector、生成、全厳格ゲートは固定。補助canonical正例露出とmain露出は別計数する。

43テスト、データ35ファイル一致、全189166行の境界/mask、256組の原文・source SHA・token再符号化・連結、勾配、RNG、初期full DEV、Adam/momentsを検証し、410入力を凍結した。200/1000更新でR40とmain対象数・バイト数・Python/Torch RNGが完全一致。

## 実1000更新の中間診断（最終採用判定ではない）

| 指標 | R40同時点 | R41同時点 |
|---|---:|---:|
| 共通DEV NLL/byte | 0.96973824 | 0.96980185 |
| 人間会話DEV99 NLL/byte | 0.94404859 | 0.94344914 |
| TRAIN64 correct-context NLL/token | 3.57244381 | 3.56588296 |
| TRAIN64 context gain | 0.09825191 | 0.09705597 |
| 日常12全文意味primary | 0 | 0 |
| 日常12長期loop primary | 4 | 2 |
| 日常12 EOS | 10 | 10 |

新12全文を実際に読み、旧12は凍結manifest SHAと全raw core一致の後に既存読解を参照。6件は旧新で全文/token/EOS等が同じ。短い「今日は」反復、90tokensの有限説明を広いloopに含めれば新4件となる。「公園とか行くのですか？」を省略された予定確認と許せば新whole1という感度を残すが、primaryでは既出の予定への自然な接続が弱く0。原文を修正せず、[全24生成](execution/paired-daily-generation-1000/FULL_GENERATIONS.md)と[読解・感度](execution/paired-daily-generation-1000/reading-complete.json)を保存する。

中間評価はraw Python FP32のみで、JS/export parityはまだ測定していない。TRAIN64は文書が重なる既存TRAIN診断でheldout/TESTではない。NLL改善や短縮だけで意味・文脈理解の改善とはしない。元の厳格ゲートは10000後の実全文で評価する。研究anchor R25と公開モデル/サイトを維持する。
