# Round34 結果 — 発話境界への自己負例prefix整合

実際のoptimizer更新10000回を1度完了。自然な日常会話の改善は実証できず、標準採用を見送る。研究anchorはRound25、公開モデル・サイトは変更していない。選択された重みは8000回、終了時は10000回で、両者の新しい全文84件を実際に読んだ。旧2状態を含む168状態出力の全文は[ALL_FOUR_STATE_GENERATIONS.md](execution/ALL_FOUR_STATE_GENERATIONS.md)、個別理由と感度はexecution内のmanual/reading JSONに保存した。旧モデルの全84件を今回新しく読み直したという主張ではない。

## 比較条件と実行

Round33と同じRound28 latestモデル・Adam20000・Torch/privatePython RNG（重みlineage59000）から、同じ10000更新を行う兄弟比較。変更はhuman最初の抽出行で自己生成負例を始めるprefix終点だけ。元の32token内、8token以上の既存token整合済み発話区切りの最後を選び、適格な区切り・文字開始がなければ従来に戻す。prefix長も短くなるので、純粋な境界効果とは分離していない。

独自8層×192、heads4、FFN768、context256、語彙5455、4655808parameters、通常/Glyph/ランダム境界BPE40/30/30、human30%と旧ジャンル70%、batch8、CPU2threads FP32、seed2049、LR2.2499999999999998e-5、teacher4gramUL1.0と自己生成UL0.1/every10、greedy負例64は固定。正解文・抽出・語彙・推論条件の変更はない。全10000のpositive抽出順、15584824target tokens、54383388target bytes、最終Torch/Python RNGがR33と一致。自己負例1000回のうちhuman296回、prefix変更252回。全重み・momentsは有限で、固定367入力のSHAも訓練後一致した。

latest full checkpoint SHA `8f908974cf5d5f6852e9a0f06741048f01c7e4fa2789f56601ff1a7deb78e315`、Adam30000・lineage69000。selected8000 full checkpoint SHA `572d893a618d049de7e995ab677c4f0e984f1fa05e166dbc3f943d698f6a23c0`、Adam28000・lineage67000。model.js/selected-weights.ptは推論用で、optimizer再開にはfull stateを使う。zero、actual200/1000/5000、selected8000、latest10000の損失のないpartsとSHAを保持している。兄弟R33の更新をR34の系統へ加算しない。

## 実測

| 項目 | R33 selected8000 | R34 selected8000 | R33 terminal10000 | R34 terminal10000 |
|---|---:|---:|---:|---:|
| 共通DEV NLL/byte | 0.967679077629 | 0.967689158775 | 0.968971745650 | 0.968907478051 |
| 従来17 初文合格 | 10 | 10 | 7 | 8 |
| 従来17 非長期ループ | 5 | 5 | 5 | 6 |
| 従来17 全文意味・主判定 | 2 | 2 | 0 | 1 |
| 日常12 全文意味 | 0 | 0 | 0 | 0 |
| 日常12 長期ループ・主判定 | 11 | 10 | 10 | 11 |
| authentic native8 全文意味 | 0 | 0 | 0 | 0 |
| 固定MRMP5 全文意味 | 0 | 0 | 0 | 0 |

共通DEV初期値は0.971898957127。選択NLLはR33より約1.01e-5高い。終了時は約6.43e-5低いが、selectorを終了時へ変更しない。17/13/9の全scope、narrative/contemporaryの両群で従来の厳格ゲートは両新状態とも不合格。閾値や未知名・創作の扱いは変更していない。

selectedの全文意味2件はENV05の有限の法令・資源施策文群と、MDN02のメソッドが別メソッドを返す一文。法名・年号・API仕様の事実正確性は認定しない。指示対象や型説明の弱さを重く見る保守的感度は0件。terminalの1件はSTAT00の情報提供時の利用方法を紹介する短いEOS文で、対象を文脈から補う読み方に依存する。対象未解決とみる保守的感度は0件。日常会話の成功にはいずれも数えない。

selected日常12の週末返答は、前回の長い相槌周期から有限の食事場面へ移ったが、質問への返答にならず意味0。天気予報文群の例は旧と全文同一で、非長期ループという主判定を維持した。選択状態のloop10は強い反復を数える感度で12、有限の質問・食事・独語を許容する感度で7。終了時のloop11も感度10〜12を保存した。どの読み方でも日常の全文意味0は変わらない。native8/source5は両状態とも全件長い反復、EOS0。source5は1cast family・3公開IDであり5独立集団ではない。

会話DEV99 NLLはR33selected0.905771475585→R34selected0.905768835509、R34terminal0.902266398694。固定TRAIN99は0.869664846050→0.869650598885→0.864932415787、gapは0.03610663→0.03611824→0.03733398。TRAIN99は全TRAIN平均でも全target既見の証明でもなく、DEVとの長さ・話題も揃えていない。両lossが下がる中のgap変化だけで過学習と断定しない。R34positive抽出はR33と完全一致するため、同一親からのraw target-byte coverageもR33実測58.1692%→82.6867%と同じ。これは意味や文脈のカバー率ではない。

## 失敗と原因の切り分け

- 容量: R27のFFN拡大でも日常意味は増えなかった。幅・深さ全般の容量不足は否定できないが、今回の結果だけで大規模化を選ばない。
- データ・ジャンル: human30%でも公的文書・天気・技術・物語への逸脱が残る。終了時の週末例では既存TRAIN由来の図解注意書きも出る。R33で固定したJMA HTMLとtext-node抽出の証拠を参照し、画像や第三者図解の利用権を拡張して認定しない。今回caption削除や新規データ追加は混ぜていない。
- 分割・境界: 1000TRAIN自己生成と新84状態出力はUTF-8/tokenが有効。真の発話末尾へ負例prefixを合わせても日常意味は改善しなかった。文字境界だけを主因にはできず、BPE一般やprefix短縮との交互作用は未分離。
- LR・optimizer: 初期model/moments/RNG、実更新カウンタ、有限性を確認。R33/R34のNLL波形はほぼ重なり、8千回後の戻りも共有する。状態不一致の証拠はないが、LR最適性を証明したわけではない。
- context: 256token上限が未完を作る例はあるが、上限前から主述・意味が崩れ、EOSでも不成立な例がある。contextだけで説明できず、長文化は今回未検証。
- 学習不足・過学習: R33の継続doseでNLLは改善した一方、日常全文0は続いた。今回も単純な追加回数を次策にせず、TRAIN99/DEV99の限界を残す。
- 数値誤差: selected42/42とterminal42/42でPy/JSの全文、およびraw FP32/7桁exportの全文が一致。測定した意味崩れはこの差では説明されない。旧controlの現runtime raw比較は25件、orig17は今回再実行していない。過去R10のnear-tie分岐16/17は別証拠として保存し、tol2e-4も変更しない。普遍的一致とは主張しない。
- 評価: 全て露出DEV・1seed・assistant読解。新TESTや独立盲検ではない。humanDEV99に完全重複1組がある。100回ごとのtraining lossログは全てevery10の自己負例更新に当たるので、全更新の平均総lossとして読まない。検証NLLは純CEで別物。固定16prefixのsaturation旧比較はanchorR25で、科学比較元R33ではない。古いcanonical gapもhumanや全expanded TRAINを測るものではない。詳細はdiagnostic-comparator-scopes.json。

## 実装修復と検証

主要pipelineはexit0。固定source5だけ、凍結wrapperのmodel allowlistにR28が残りR33比較がassertで失敗した。元コード・失敗ログ・SHAを保持し、allowlistのR28→R33だけを変えた別evaluate_control33.pyと回復launcherで測定した。推論数学・入力・重み・選択・学習は変更せず、追加optimizer更新0。recovery JSONに逆patch一致と証拠を記録。次の準備ではこのallowlist整合も事前検査する。

Node repository962/962、既存公開モデル回帰2580/2580。公開モデルの試験成功を実験モデルの言語合格とはしない。初期367入力とR33最終456成果物のSHAを再確認した。最終manifestはpartsと復元SHAを含めて検証し、学習未実施を完了として記録していない。

## 採否と次の1条件

標準採用なし。R33に対するprimary ParetoはNLLの微小悪化で不成立。採用anchorR25に対するprimary Paretoは成立し任意のNLL-only保持は可能だが必須ではない。実用目的である日常意味0と解釈依存から昇格しない。公開挙動は維持する。

次はR34と同じR28 initial full state・同じ10000更新の兄弟比較で、変更はhumanの真の発話末尾へのEOS補助CEだけ。元goldが単独改行ID16で、既存mask内のTRAIN実発話境界に限りEOS2の損失を1.0で追加し、元のvalid-target数で正規化する。元gold・抽出・R34prefix policy・BPE・モデル・LR・seed・selector・推論は維持。会話単位EOSは各view8975に対し発話区切りは約26万であり、native/sourceが終われず反復することが根拠。全147986行の候補maskと合成logitの数学を準備検査済みだが、実モデル学習は別Round35として条件凍結・勾配・checkpoint・初期DEVを確認後に行う。補助対象は旧抽出再生で約1%の元target数。終了しやすさは意味成立を保証せず、早すぎる終了や無関係な短答は失敗とする。データ追加・caption整理・BOS変更・係数sweepや大規模化を同じroundへ混ぜない。
