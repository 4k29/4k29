# R41 結果 — 正しい文脈CEへの変更、実10000更新完了・不採用

**実際のoptimizer更新10000回を完了。日常12件の全文意味成立は0→0、従来の全厳格言語ゲートは未達で、不採用。** 人間会話DEV99のNLLは改善したが、原文native8の最小の自然な会話行為は3→2、source5は1→0となり、自然な全文生成の改善は実証されなかった。研究anchor R25、公開モデルとWebサイトの挙動は維持する。merge/deployはしていない。

## 今回変えた条件

変更は補助損失の形式だけ。`softplus(correctMeanNll - wrongMeanNll).mean()`を`correctMeanNll.mean()`へ変更した。同じ元の人間発話を正しい2発話文脈から予測する。不一致文脈のforwardとNLL記録は診断として残すが、学習損失・勾配に寄与しない。wrong文脈を変えてもloss/gradientが一致するテストと、正例だけのCE/mask照合を実施した。

科学対照R40、補助なしR39は履歴参照。R40terminalの延長ではなく、同じR28 latestのfull model/Adam20000/Torch・private Python RNGからの兄弟比較。独自8層×192、4heads、FFN768、context256、5455語彙、4655808params、CPU2/FP32/deterministic、batch8、LR2.2499999999999998e-5、seed lineage2049、weight decay0.05/clip1を保持。teacher4gram UL1、self-negative UL0.1/every10/greedy64、真の人間発話末尾EOS補助0.3、競合する元のNLだけmain CEから除外し元の分母を保持する既存目的も同一。

main BPE40/30/30、source RealPersona25%/JMRD5%・非人間70%、全mainデータ、同じTRAIN原文256組・係数0.1/every10/batch2/cyclic/eval＋fork_rng、DEV selector（0/every500の最小共通NLL）、全生成・ゲートを固定。**補助のcanonical追加露出はmainの40/30/30とは別計数。全目的を合算した比率が40/30/30という主張はしない。** 原文の修正、新規取得、外部モデル/Tokenizer/API/teacher正例/固定回答はない。

単一2組batchのaux勾配normは17.32754045、係数込みで3行の人間CE勾配normに対し0.34449076。係数は勾配を見る前に固定し探索なし。これは全pool・全合成目的・学習後のnorm保証ではない。損失形式による勾配規模とglobal clipへの作用の違いも今回の変更に含み、純粋な意味機構だけの分離とはしない。

## 実行・データ・保存

43 Python契約テスト、35データファイル一致、189166行の境界/mask、原典TRAIN JSONのSHA・元発話・再tokenize・連結、勾配、Adam/moments/RNG、初期full DEV完全一致を開始前に検証。410入力を凍結した。全256poolはR40で読んだ既存対象を再利用し、新たに意味filterや再選別を行わない。元の誤字と漢字span proxyの限界を保つ。

実10000更新、Adam counter30000。選択状態は9000/Adam29000、weight lineage68000、terminal lineage69000。途中の再開・再訓練はなく、記録された訓練時間は9188.715355845秒。予定回数を完了数へ置き換えていない。R40と初期full state、main抽出・対象数・bytes・最終Python/Torch RNGが完全一致し、200/1000/5000の対応状態も検証した。

mainは15578400targets/54368222bytes/80000row draws。実view drawsは32003/23922/24075、RP20124/JMRD4055/other55821。補助は実1000呼出/2000組、正例47833targets、診断を含む両文脈95666scored targets/276126inputs。256組すべて使用。wrong側のscored数はgradient対象数ではない。自己negative1000回・38606生成tokens・14206反復位置、1000/1000 UTF8 valid。

100個の実log合成lossは固定係数と一致しfinite。0/every500の21 full DEV点、old/new各100点の瞬間mini-batch loss、1000点のaux traceを保存した。瞬間lossは全TRAIN平均ではなく、形式の異なる合成lossの旧新大小をそのまま優劣に使わない。aux曲線も毎回の2組の学習前lossであり、全pool平均ではない。

initial0/200/1000/5000/selected9000/latest10000の6役割でfull model/optimizer/RNGとlossless partsを保存。保存候補weightsとJS exportは採用を意味しない。旧実験の無視対象raw復元コピーを消す前に、Git追跡済partsの個別/連結/raw SHAを検証し、全凍結入力を保護した。唯一の重み/moments/RNGは失っていない。200状態のraw重複追跡もpartsを保持して修正し、履歴を改変していない。

## 同条件の生成・NLL比較

各roundは実10000更新済み。selectedは両方9000、terminalは両方10000。元の同じ42入力、全語彙greedy192、Python1thread、修正・検索・template・デコード抑制なし。旧selected42は再生成した全coreの一致と凍結manifest SHAを確認して既存判定を参照し、旧terminal42は検証済履歴。新84全文/prefixはすべて実際に読んだ（非盲検assistant判定）。新84には77個の異なるprefix/fulltext対があり、重複7件の判定は一致。同じ初文59照合のcomponentもR39/R40/R41を通じ一致した。

| 指標 | R40 selected9000 | R41 selected9000 | R40 terminal10000 | R41 terminal10000 |
|---|---:|---:|---:|---:|
| 共通DEV NLL/byte | 0.96533725 | 0.96539240 | 0.96566916 | 0.96586334 |
| 人間会話DEV99 NLL/byte | 0.93459819 | 0.93383869 | 0.93403724 | 0.93299269 |
| 固定RP TRAIN99 NLL/byte | 0.90709983 | 0.90622504 | 0.90553495 | 0.90420895 |
| 原17 初文合格 | 6 | 7 | 7 | 6 |
| 原17 非長期loop全文 | 2 | 3 | 4 | 2 |
| 原17 全文意味 | 0 | 0 | 0 | 0 |
| 日常12 全文意味 | 0 | 0 | 0 | 0 |
| 日常12 長期loop primary | 4 | 3 | 7 | 6 |
| 日常12 EOS | 8 | 9 | 6 | 6 |
| 原文native8 全文意味 | 3 | 2 | 2 | 2 |
| 原文native8 長期loop primary | 1 | 2 | 3 | 1 |
| 原文native8 EOS | 8 | 8 | 7 | 7 |
| 固定source5 全文意味 | 1 | 0 | 0 | 0 |
| 固定source5 長期loop primary | 1 | 2 | 2 | 2 |
| 固定source5 EOS | 4 | 4 | 3 | 3 |

[全168出力](execution/ALL_FOUR_STATE_GENERATIONS.md) SHA `e207c31837df470a05a1465182bc0489dc257cefb4f2b546ff59df4fb0031893`。全token IDs/EOS/UTF8 flagも元JSONに保持。168独立問題ではなく同じ42入力×4状態である。

初文の最低grammar2・connection2・total9・閉文/valid tokens、17/13/9各scopeで物語/説明文それぞれ初文80%・非loop90%・全文意味80%を維持し、両状態とも全gate未達。固定human bound0.9107185711429243も未達。paired human/daily非悪化guardは通るが、strict gate、固定guard、科学対照/anchor Paretoが通らず不採用。NLLだけの例外採用はしない。

### 実際の出力と判定境界

- 待ち合わせの時刻の問いへの新selected全文は「天気の毒が出るのか？」。短いEOSでも語結合と文脈が成立しない。
- バイクのレストアの話への新selected全文は「そうですね！おいしいですね！」。挨拶やバイクを味覚へ結ぶ手掛かりがない。
- 酸っぱい飲料を飲む方法の話への新selected全文は「おいしいですね。おいしいですね。おいしいですね。」。18tokensEOSでも三文同一の停滞をprimary loopとした。短い強調と読む非loop代替も保存し、EOSだけで意味成立にしない。
- 女優が好きという原文への「そうですね！私も好きです！」は普通の対象省略を認め、旧新とも自然な最小の好み共有と判定する。具体的対象名・新情報を生成したことにはしない。
- source2の旧selected「そうですね。」は最小の自然な同意だが、新「そうですね。あとは？」は何を追加で問うかが曖昧でprimary0。場所を尋ねる省略という代替1も残す。後続が増えただけで改善とはしない。
- 新terminalの仕事帰りへの「行きたいと思います！」は文法的に閉じる。行先の先行文脈がなくprimary0だが、普通の省略と許せば1。文法破綻という失敗理由にはしていない。

日常selectedの97tokensの疲れ応答は同じ長い句を二度含むが、その後別の問い/相槌に移る有限の侵入反復と長期loopを分けた（primary loops3、広い代替4）。terminalの日常はprimary6/広い代替7。native selectedの短い三連同意を非loopに寄せればloops1（primary2）、terminalの43tokensの三種相槌を広くloopとすればloops2（primary1）。native selectedの既存の曖昧な確認を許せばwhole3（primary2）。source selectedは推薦/購入場所の補いでwhole2、terminalは推薦/場所/未明示の予定等の補いで3（いずれもprimary0）。primary/代替を混ぜて改善を作らない。架空の名称・数値の外部真偽、末尾cut、単に新情報がないことだけを失格理由にしない。

nativeの意味成立2件は好み/味の最小共有で、新両状態とも明示的context object参照0・新情報0。source5はONE cast family/3 public pseudonymous speakers。元の17・assistant作成日常12・native8・source5は繰り返し露出したDEVで、新TESTや未見話者母集団の一般化を意味しない。human99にも完全重複1組があり、独立99標本という推測統計をしない。

## 文脈診断・学習対象への適応

全て同じ固定TRAIN64と補助256。64組は補助と同一の(document,turn)を含まないが、TRAIN/source文書に重なりがありheldout/TESTではない。

| 指標 | R40 selected | R41 selected | R40 terminal | R41 terminal |
|---|---:|---:|---:|---:|
| TRAIN診断64 correct NLL/token | 3.48819817 | 3.47147597 | 3.48251884 | 3.46555066 |
| TRAIN診断64 wrong NLL/token | 3.60092353 | 3.57369694 | 3.59834734 | 3.56938566 |
| TRAIN診断64 wrong−correct | 0.11272536 | 0.10222097 | 0.11582850 | 0.10383499 |
| TRAIN診断64 gap正の組 | 49 | 47 | 46 | 48 |
| 補助pool256 correct NLL/token | 3.56841944 | 3.21587364 | 3.55003925 | 3.17839164 |
| 補助pool256 wrong NLL/token | 3.93401707 | 3.54272525 | 3.92394980 | 3.51034281 |
| 補助pool256 wrong−correct | 0.36559763 | 0.32685160 | 0.37391055 | 0.33195117 |
| 補助pool256 gap正の組 | 253 | 253 | 254 | 253 |

正しい文脈のNLLは改善し、wrong NLLも下がるためgapは減った。poolの大きな適応と64組/DEVへの小さな移行は確認できるが、全文意味の改善へは移らなかった。局所適応と整合する一方、逐語暗記・全TRAIN過学習・全く文脈を使わないという断定はしない。loss/gap単独を言語能力の代用にしない。

共通DEVは従来の7サイトの物語・行政・技術で、人間会話99とは対象・serialization/窓が異なる。共通DEVはcanonical自体も悪化しており、単にglyph/random viewだけの交換ではない。

| 共通DEV selected view | R40 | R41 | 新−旧 |
|---|---:|---:|---:|
| 0 | 0.94679841 | 0.94686136 | +0.00006295 |
| 1 | 0.98293223 | 0.98299726 | +0.00006504 |
| 2 | 0.97246073 | 0.97249559 | +0.00003486 |

固定RP TRAIN99 NLLは0.90709983→0.90622504、DEV0.93459819→0.93383869、gap0.02749837→0.02761366。terminalはTRAIN0.90420895/DEV0.93299269。これは旧RP subsetで、追加JMRDを含む全TRAIN平均ではない。TRAIN/DEVの話題・長さも対応させていない。human NLL最良のterminalへselectorを変えると、原17の初文/非loopはselected7/3から6/2、日常loopsは3から6へ悪化しており、lossだけのselector変更を選ばない。

中間1000ではhuman NLL0.94404859→0.94344914、全文意味0→0、日常loops primary4→2（広い代替4）、EOS10→10。5000ではhuman0.94185127→0.94103058で、計画どおり自由生成は追加していない。中間はraw Python FP32のみでJS/export一致を主張しない。[中間24全文](execution/paired-daily-generation-1000/FULL_GENERATIONS.md)と最終結果を混同しない。

## 原因候補の切り分け

| 候補 | 今回の根拠と残る不確実性 |
|---|---|
| 容量 | 4.66Mで局所poolへの適応は可能だが、広い文法/意味の表現不足は未否定。R27の限定的FFN拡大でも日常全文0だったことは全ての大規模化の否定ではないが、直ちに拡大する根拠にもならない。 |
| データ量・偏り | main原文と抽出は完全同一。補助は163正例文書/45donor文書/49prefixと長い漢字spanに偏り、元の誤字も残る。pool NLLの大幅改善に比べDEV移行が小さく、生成の対象参照が増えない。元の対照のため残した選別がCEに適切かは未解決。 |
| 分割・文字境界 | own BPE/語彙/境界と全main viewsは固定。新84と自己negative1000でUTF8 validであり、今回の失敗をbyte破損では説明しない。天気の毒等の語結合と形態境界の問題は未否定。分割比変更は今回試していない。 |
| LR・optimizer・目的 | 同じ初期model/moments/RNG、finite勾配、固定LR、実counter、合成係数、main抽出の一致を検証。wrong勾配を外してcorrect NLLは改善したが全文は改善しない。規模の異なる勾配/clip作用も形式の一部で、最適LRや純粋な意味機構は証明していない。 |
| context256 | 固定42prefix＋192生成は256内で、早い時点の話題崩れもある。単なる推論window切落としだけでは説明されない。長い訓練会話への制約は未否定。 |
| 不足/過学習 | 実10000完了。選択9000以降はhuman NLLが下がっても日常反復や原17初文が悪化。小poolの局所適応と全体過学習は区別し、R33の追加doseでも日常全文0だった既存結果から単純な回数追加を自動選択しない。 |
| 推論数値 | 新84/84 Py/JS、84/84 raw/export全文一致。今回の意味崩れはこの差では説明されない。全hardware/全logits保証ではない。 |
| 評価 | 非盲検・露出DEV・曖昧な省略/loop境界・同じ入力と同じcastの相関を開示。role無し原文でも味覚への逸脱があり、role表記だけの欠陥では説明されない。旧scopeのTRAIN gap/勾配診断を今回の科学対照へ誤読しない。 |

legacy `train-development-gap.json`はR11の固定canonical rowsとR12のcacheを使う旧web診断で、R41拡張全TRAINの平均ではない。`sequence-saturation.json.models.old`は**R25 anchor selected9500**であり、R40ではない。14固定TRAIN prefixでの非zero UL勾配を示す補助情報として扱い、単一条件の主比較はpaired R40/R41に限定する。

## 数値・回帰・判定の限界

新84/84でPy/JS全文・tokens・EOS・UTF8 flagが一致、raw FP32/7桁exportも84/84一致。測定reference最大差はJS1.33514404296875e-05、raw/export2.3126602172851562e-05、tol2e-4のまま。logitsはsampled referenceで全時刻/全hardware保証ではない。旧selected JS42は現runtime、rawは追加25のみで元17は再実行せず、旧terminalは履歴。既知R10 near-tie16/17（SHA117e5f69…）を保持し隠していない。

962 repository testsと公開43質問/2580応答回帰は成功。公開挙動の保護でありR41の会話能力の証明ではない。R39のoperator policy表示範囲の事故も既存記録を保持し、operatorが全reserved内容から完全に盲検という主張はしない。R41でTEST textをモデル/Tokenizerへ渡し、loss評価・生成した結果はない。

[次の単一条件候補](NEXT_EXPERIMENT.md)は未実装・実更新0。R41は採用せず、R25 anchorと公開挙動を維持する。

## 主なSHA（完全一覧はmanifest）

- policy: `044cae69e4d2d1546a352a224b3202507e0cd27ec6863414701208a6ec9c8c0d`
- trainer: `d76bb5b1892e0b2dfdf4a64a1c8f67a37122f5e34b4120425be073d1b92fe46a`
- frozen source manifest: `ddfe3b03ea32e5dcb7c691b131e6b0f61dd228a02027199b401ae714879efdbc`
- tokenizer: `453e93eafe8bf745e47c5241f9c7e9ed9e0b7dd3dc2bb912c21255b654bf5613`
- main train tokens: `a465b071db720c46d1efe74821e4a9609d19e183f2af35f290f4681e17e63a98`
- auxiliary pool: `0b1a268288d13e1c37a0c561509a33c0871deb69c6a38c6231762c5dba7991ae`
- full raw-text assembly: `e207c31837df470a05a1465182bc0489dc257cefb4f2b546ff59df4fb0031893`

| full model/optimizer/RNG role | SHA256 |
|---|---|
| initial0 | `abd011661a02a7083e1609b5919ac9b493480080788d12d5bba07dd8b7013104` |
| 200 | `ab0e7649bb6021a17a3e65f7cf46689d472a21df35d7bd0581925c931984ed49` |
| 1000 | `b21529e7eddbefdbc31d970bd9567c66b59f74018916a02f8ba5f75da55baaaf` |
| 5000 | `dbc6d58fb6311d2def2528b71d31a1e91f5e0510a25c28f0530797a31f84363c` |
| selected9000 | `2aae53291d75af683141cfccbe5e622d42f49e5cc76dd850f9c075635333aee8` |
| latest10000 | `f2493f26cb01e92244d9f4487b26a8a0ba598e5b5ed2a838bfad4a5fc66beaa1` |
