# conversation-v2：開発方針の転換と初回実行結果

2026-10-26（日本時間）。GOAL.mdを最上位とし、自然な日本語で内容のある日常会話を行うことを目標に、新系列を実装・学習した。

**結論：新しい独自モデル系列・TRAINのみのTokenizer・原典会話構造・評価基盤を実装し、約438万/1,123万parametersの2モデルを実学習した。しかし、この初期学習では内容を伴う適切な返答は両方0/32で、対話能力の改善やPhase1達成とは判定しない。**

CPUでの基盤pilotは完了。正式採用・公開置換・マージはNo-Go。外部学習済み重み/Tokenizer、外部生成API、別モデルの生成正解、検索回答、出力修正は使っていない。

## 方針の変更

旧466万規模・既存loss改良に固執せず、既存資産を保存したまま`conversation-v2`を独立branchで構築した。保持CE等の小比較を完了すること自体を目的にしない。

旧R47/R48事前検証/文脈利用/64組診断から、token予測と意味の通る全文は別、狭い暗記と転移は別と判断した。R48全量集中のNo-Goは維持。新基盤とR46の差は多因子なので、幅の因果比較は新系列2モデルの間だけに限定する。

新しい研究順序は、現代日本語の基盤生成→人間が書いた適切な応答への追加学習→自己返答を含む複数ターン→知識/推論→汎用対話。具体的な能力・phase移行条件はSTRATEGY.md/evaluation-design.md。今回のmodeは**人間A/B会話の継続**で、AIとしての指示追従や人格を学習したとは呼ばない。

## 監査・実装

| 項目 | 実施結果 |
|---|---|
| 既存データ | canonical view約1,108万tokens、人間会話約751万。3viewsは独立原文3倍ではない。旧samplingの非会話55%には古典・英語技術・行政等が含まれる |
| 原典/権利 | 既存人間TRAIN原典/CC-BY-SA4、全RP8,975原典SHA・269,877発話/ordinal/埋込改行を監査。出典とlicenseを保持 |
| 新split | TRAIN5,986会話/180,006発話、DEV255会話/7,661発話。永続話者・文書family分離。cross-speaker2,722、以前露出したDEV12会話を隔離 |
| 新Tokenizer | 新TRAINのみから自作glyph+BPE、3,997語彙。旧の学習済み語彙/mergeを継承しない。400k文字未満のTRAIN sampleで512word merges、glyph inventoryもTRAINのみ |
| 品質/境界 | 全13,878窓、2,816,905教師位置がdoc初BOSを除き各1回、180,006真EOSが各1回。PAD教師位置0、文書混合0、本文byte復元。発話内改行を別発話に誤分割しない |
| データ規模 | 本文4,177,579文字/2,456,893body tokens。role/EOS/BOS込み2,822,891stream tokens。DEV未知glyph19種21出現をbytefallbackで保持 |
| 重複/漏洩 | 新DEV32履歴＋goldの完全一致TRAIN重複0、gold単独一致2（自然な短表現）。Tokenizer fit sample580会話すべてTRAIN。semanticな質問family全分離まで証明したわけではない |
| 学習基盤 | 既存独自Decoderの数学を再利用、fresh random weights/fresh AdamW。role3/4は人間A/B、EOS2は真の発話末尾、BOS1は文書開始。普通CEで全causal targets、PAD除外 |

新系列では全てを会話にすることが最適だとは断定しない。今回は日常会話に集中する第一pilotとしてRPのみ。JMRD映画雑談や新しい現代日本語原文の用途/偏り/利用条件はDATA_STRATEGY.md。新しい大規模原文、CEJC、有料データ等を取得済み/利用許可済みとは記録しない。

## モデルと計算資源

|  | small | medium |
|---|---:|---:|
| parameters | 4,375,872 | 11,225,280 |
| layers / heads / context | 8 / 4 / 256 | 8 / 4 / 256 |
| width / FFN | 192 / 768 | 320 / 1280 |
| 実optimizer.step | 514 | 514 |
| 保持更新 / 再開replay | 512 / 2 | 512 / 2 |
| terminal Adam counter | 512 | 512 |
| 保持target positions | 415,321 | 415,321 |
| body / EOS / role targets | 361,960 / 26,667 / 26,694 | 同一 |
| 異なる窓 | 2,048 | 同一 |
| window epoch | 0.14757 | 同一 |
| 学習時間 | 197.22秒 | 366.44秒 |
| 最大process RSS | 約680MiB | 約926MiB |

合計実更新**1,028**、保持1,024、replay4。launch全体568.77秒。CPU quota2core、hardRAM8GiB、GPU無し。事前のCPU学習全体30分上限内で完了し、有料GPU/新環境は開始していない。

同じ窓ID/本文・EOS・role dose/学習率/sampler順序で幅だけを変えた。全512batchが一致。初期seedは同じだがtensor形状は違い、dropoutの乱数消費も幅に依存する。1seed、同token量、同LR scheduleであり、同FLOPs・最適化済みの容量比較ではない。AdamW3e-4、64warmup、512までcosine/min3e-5、clip1、FP32は事前固定。

step2のdisk stateから3/4を再実行し、model/Adam/RNG/sampler/全traceが連続実行と完全一致。replayも実更新に算入。両100parameter optimizer statesは有限、moments非負。初期state実物は最新checkpointで上書きされており、fresh初期化は固定code/seed/起動記録・optimizer再生成からの由来確認。初期実物とのbitwise比較と偽らない。

### 数値事前検証の修正

初回medium勾配監査は、標準FP32 global normとFP64参照の相対差最大約3.86e-5が元2e-5基準を超えて停止した。全勾配は有限。新系列両モデルを**FP64でnormを集約し、同じ係数をFP32勾配に掛ける**共通clippingへ変更し、maxnorm1/epsilon1e-6/許容差/FP32学習は維持した。参照相対差は約1e-13。旧production実装は変更せず、初回失敗・旧SHA・修正・再監査を保存した。全て本学習前、optimizer0回時点。

### 大きい候補の比較

| 候補（新語彙で算出） | context | FP32 Adam param/grad/moments概算 | fullstate概算 | 計画用20N tokens |
|---|---:|---:|---:|---:|
| 11.31m | 512 | 181MB＋activations等 | 136MB | 226m |
| 27.53m | 512 | 440MB＋activations等 | 330MB | 551m |
| 60.56m | 1024 | 969MB＋activations等 | 727MB | 1.21b |

これら3行は計画値で、GPUで構築/訓練したという記録ではない。正確な式/6NT/20N〜50N例/throughput仮定はresource-comparison.json。20Nは成功保証・最適点ではない。現在の約282万stream tokensを80〜429回再読するだけでは情報が増えない。大規模化にはデータと計算を同時に監査する。

現在のメモリで12mを動かすことはできたが、数億tokensの基盤学習は別問題。中型実測は約1,133total-target tokens/sec（このCPU/context/batchだけ）。2億tokensは単純換算約49時間。GPU8〜24GB以上と数十〜100GB級のデータ/保存領域を候補とし、実機のactivation memory/throughput/予算確認前には開始しない。

## 固定評価と結果

新系列にとって学習・Tokenizer未露出の32文書/話者DEV、64TF窓。各モデル32件をfull-vocabulary greedy192、真EOS、無修正で生成。4episode×3turnを自分の生成履歴で継続し、EOSを捏造せず、必要なら古い完整turnだけを落とす実装。今回は全episodeで履歴削除0。

R46参考は旧BPE/plain履歴。原典はR46の旧TRAINで既露出、frame/Tokenizer/学習量も違う。32件TFは可能、同じ192上限で無crop生成できるのは23件のみ、残り9はunsupportedとして保存。**旧23対新32の単純な成功率比較や共通未知TESTとは呼ばない。** paired23と新全32を別集計。

単発87全文（新64＋旧23）を条件名/gold/指標を伏せて独立Evaluation Analystが実読、新64をModel Researcherが別に実読、自己継続8episode/24turnも全文と実入力を読んだ。独立人間評価ではなくassistant評価で、原典既読/重複からの推測/主観の限界は記録。

| 新系列DEV32 | small | medium |
|---|---:|---:|
| DEV64窓・body NLL/token | 6.0072 | 5.7570 |
| DEV64窓・EOS NLL/token | 0.6154 | 0.5760 |
| DEV64窓・role NLL/token | 0.0961 | 0.0504 |
| 同じ32原文body NLL/UTF8byte | 1.1096 | 1.0595 |
| 実EOS停止 | 32/32 | 32/32 |
| 文法的に自然な全文 | 32/32 | 30/32 |
| 最小限許容される適切な全文 | 22/32（不確定2） | 23/32（不確定2） |
| **内容を伴う適切な全文** | **0/32** | **0/32** |
| 内容必須の5caseへの適切な内容 | 0/5 | 0/5 |
| 有害反復 | 0/32 | 2/32 |
| 単発の異なる全文 | 2 | 3 |
| 有意味な自己継続episode | 0/4 | 0/4 |

mediumは本文予測を改善したが、事前のpilot signal（複合全文+4/32かつ有害反復/invalidUTF8非増）は満たさない。複合成功は22→23で+1、有害反復0→2。**mediumを言語能力で勝者/採用とはしない。**

smallは「そうなんです。」「そうなんですね。」、mediumは主に「そうなんですね。」と2種の崩れた反復だった。例えば活動/希望を尋ねる会話に相槌だけを返し、適切な内容はない。これはコードの固定回答や検索ではなく、実学習した自作Decoderのgreedyが頻出相槌へ偏った結果。入力で多少文面が変わっても文脈理解の成功にはしない。

自己継続は両4episodeすべて3turnでEOS停止したが、同じ相槌を3回重ねる。クロスturn有害反復8/8、episode意味成立0/8、全原典履歴が実入力に残った。context切捨てによる忘却が原因とは言えず、これを人間との対話成功率とも呼ばない。

旧R46の同じraw target32のbyteNLL0.7539は参考値。新旧token数が420対605なのでNLL/tokenを横比較しない。旧paired23の複合2/23に対し新paired23は各17/23だが、全て最小限の相槌でspecificは新旧とも0。露出/入力形式差もあり、汎用会話の改善という結論に使わない。

### 評価・入力契約の残る問題

- 現32はSHA選択でintent-balancedではなく、内容必須5/32、内容機会30/32。相槌でも最低限成立するcaseが多い。複合45/64を内容理解成功や新言語ゲート合格としない。将来252件benchmark、文脈最小対、独立sealed source、日本語母語の人間ratersは未収集/未確保。
- 終端採点の操作化に差があった。主Evaluatorは適切な意味の発話を真EOSで終える条件、独立Model readerは文法形式/EOSを評価した。原採点を変更せず、終端値は混算禁止。主比較は全87を同rubricで読んだEvaluator。content0/64と自己継続失敗は一致する。
- **post-output静的監査**で、TRAIN文書開始は常に[BOS,role3]、DEV切出し19/32は原典local role保持の[BOS,role4]と判明。原典の話者順序は正しいが、切出し時のrole原点の分布が違う。現在のbenchmark/点数を入れ替えずframing-audit.jsonに保存。残るrole3側13件も内容応答0だが、因果寄与は測っていない。次段階前に入力契約を統一し、補正を過去の成績へ混ぜない。
- 次段階用のhuman-role rebase helperと3静的テストを追加した。body/EOS/identity alternationが全32入力で保存されることを確認したが、**現在の推論・学習・点数には未使用**。新契約下では現512と将来checkpointの両方を同条件で評価する必要がある。
- 新モデルは約0.148epoch、1seed、greedyのみ。全原典を一度読むことすら終わっていない。容量の限界、最適規模、データ戦略全体の成否、長contextの必要量を断定できない。

## Python/JavaScriptと再現性

元8975SHA、コード/データ/Tokenizer/窓・PAD/真EOS位置、実更新ledger、全loss/gradient/clipping/LR/RNG/sampler、終端fullstateと固定256weightsを保存。終端fullstateはlossless chunks。selected=terminal512でloss選択なし、256は今回の評価に未使用。

Python/JSはrawFP32を丸めずbinary化し、同じ先頭3prefix×両モデルで最大4tokenだけを事前固定して比較。最大logit差small3.81e-6/medium2.38e-6、argmax不一致0、独立greedy分岐0、許容2e-4超過0。**全192/全32や新UIを保証する検証ではない。** 既知R10 near-tie等の旧報告は維持する。

新Tokenizerは531固定入力（TRAIN256＋DEV256＋未知19glyph）でPython/JS token ID差0、UTF8往復差0。これはencodeのみで、旧prompt APIの正規化/turn5形式をそのままv2に使えるという証明ではない。既存の公開推論ソースは変更していない。

## 次の研究判断

技術pilotはGo/完了、自然な対話能力・Phase1・採用はNo-Go。モデル規模拡大だけで改善したという証拠は得られていないが、極少coverageなので大規模化が無効という証拠にもならない。

次の実行可能なmilestoneは、入力契約を固定した上で、未使用約85%の原典を含む最初の1epochの学習coverageを得ること。現実測速度から両モデルの残り学習約54分＋評価、別のCPU予算60〜90分と保存headroomを必要とする。現在の30分/512上限を、成績を見て黙って延長しない。

既存512用cosineはminLR3e-5へ到達しており、totalUpdatesだけ増やすとLRが跳ねる。「同条件継続」と偽らず、terminal Adam/RNG/orderを継承する新stageで終端LR維持等を事前固定する。1epochでも約282万targets、target/paramは約0.64/0.25なので、十分な基盤学習とは呼ばない。

同時に、適法な現代日本語の多様な人間原文と内容を要する実体benchmarkを確保する。次の本研究はこの基盤を十分学習し、内容と意味のある未知応答で判定すること。小量の相槌データへ反復したり、EOS/保持CE/係数の小実験を無目的に増やしたりしない。新規の大規模化、RMSNorm/RoPE/FFN、8k/16k独自BPE、context512/1024は、必要性が見える条件を一つずつ比較する。

データ/GPU/予算が揃うまで12m以上の数億tokens学習は開始しない。既存自作重みは対照・継続資産として保持し、新系列でも無意味な再初期化を反復しない。新しいAIとしての応答には、人間の私生活をAI自身の事実として学ばせない正解データ設計も必要。

CUDA/AMP trainer・大規模sharded入力・native512/1024学習は現在未実装/未検証。GPU VRAM値は実機測定前の計画値で、確定した最低必要量や獲得済み環境ではない。CPUで可能な次段階と本格GPU学習を分ける。

**今回の成果は、自然な会話へ向けた新しい学習基盤と、実行・失敗を含む測定結果である。会話AIの実用化や言語能力獲得の成功を記録するものではない。** R25正式anchor/R46比較対象/R48No-Go、旧厳格ゲート、公開モデルとサイトを維持し、マージは行っていない。
