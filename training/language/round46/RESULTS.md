# Round46 results — actual10,000 updates

R44に対して学習率だけ2.2499999999999998e-5→4.4999999999999996e-5へ変更した。R45の係数0.2は持ち越さず、正しい文脈CE係数0.1を維持。全10core学習ファイル・資料35files・主RealPersona40%/JMRD5%・1024pool・他loss・8層192dim/4heads/FFN768/context256・own5455 BPE40/30/30・seed2049・batch8・CPU2 FP32 deterministic・実10,000dose・全評価条件はR44と同じ。Gitの前ラウンドR45と科学対照R44を混同しない。

同じR28最新full model/Adam20000/Python・Torch RNGから開始した兄弟比較で、R44/R45terminalの延長ではない。今回の実10,000を過去の兄弟実験へ累積した更新数とはしない。学習時間9294.233秒。選択は固定共通DEV最小の9,500更新/Adam29500、最終状態は10,000/Adam30000。

## 実測結果

| 指標 | R44 | R46 |
|---|---:|---:|
| selected共通DEV NLL/byte | 0.969086854892 | 0.970906426984 |
| terminal共通DEV NLL/byte | 0.969694565511 | 0.972312270495 |
| selected会話DEV99 NLL/serialized byte | 0.917695397049 | 0.908436063446 |
| terminal会話DEV99 NLL/serialized byte | 0.918483160721 | 0.908774041281 |
| selected17 初文/非loop/全文意味 | 4 / 5 / 0 | 5 / 4 / 0 |
| terminal17 初文/非loop/全文意味 | 5 / 4 / 1 | 7 / 9 / 3 |
| selected日常12 全文/loop/EOS | 0 / 3 / 10 | 0 / 4 / 10 |
| terminal日常12 全文/loop/EOS | 2 / 3 / 9 | 1 / 2 / 10 |
| selected人間会話8 全文/loop/EOS | 2 / 1 / 7 | 4 / 1 / 7 |
| terminal人間会話8 全文/loop/EOS | 1 / 4 / 6 | 2 / 2 / 7 |
| selectedsource5 全文/loop/EOS | 1 / 1 / 4 | 1 / 1 / 4 |
| terminalsource5 全文/loop/EOS | 1 / 1 / 4 | 1 / 0 / 5 |

会話NLLは明確に改善し、事前固定の上限0.9107185711429243をselected/terminalとも下回った。selectedの8件には歩きに出たいという短い共感と、収納している物を尋ねる自然な続きが増えた。terminal17では循環経済の取組を推進する文、メソッドの返却を説明する文、サイトの情報提供方法を紹介する文が短く成立した。これは説明文の意味構造の評価であり、架空のAPI名/返却仕様や政策の事実の正しさを認証しない。

一方、selected17の全文意味は0のままで、日常12件はselected0/terminal1にとどまる。selected日常のloopは3→4へ悪化。主語句、名詞修飾、同一因果節を重ねる崩壊や、時刻の質問へ料理/引用文を返す転換が残る。最初の一文や希望だけを抜き出して合格にしない。全17/13/9の両ジャンルの厳格ゲート、科学対照/採用anchorのPareto条件、paired日常非loop条件は不合格。fixed実用guardは通るが、それだけでは採用しない。**正式採用false、R25anchor・公開モデル・Webサイトは維持。**

旧新selected/terminalの168全文をALL_FOUR_STATE_GENERATIONS.mdと各JSONへ保存し、新84全文を全て実読解した。83種類のprefix+全文で、重複する日常のお願いの判定も一致。過去R39〜R45の同一全文・同一初文と照合し、初文component一致169件を確認。独立盲検人手評価ではなくAssistant実読解で、全て既存の露出済みDEV。168件を168独立問題、新しいTESTや未見話者への成功とは数えない。source5は1話者組合せfamily・3公開仮名話者の5文脈。

## 曖昧例と判定の限界

有限で異なる行政paragraphと局所stutterは長いloopから分け、侵入反復と全文失敗を別記した。terminal17の主loop8件は、短いLatin/火山名詞列/会合paragraph/法名詞連鎖もloopと取る感度では12件となる。primaryの非loop9/17だけを成功としない。未知名や外部事実の誤りだけでは文法・意味を落とさず、APIの型の階層を厳しく読むとterminal全文は3→2件となる。

日常の依頼・休息/趣味の疑問、暑い日の食事相談、現在の状況の問い、女優へのあれという参照などには普通の省略を許す/明示参照を求める別解がある。詳細はSHAを結んだreading-notes-as-executed.jsonと各manual/readingのsensitivities。primaryの一部短い成功は解釈に依存し、一般的な自然会話能力はまだ確立していない。

実1,000の24全文ではprimary全文0→0、loop5→3、EOS8→9。公園への同一の行きたいですね二文はprimary0、普通の口頭強調なら1と併記。あまり+肯定希望、未完理由節、短い名詞化stutterは短くEOSでも失敗にした。途中結果を見て条件・seed・selectorは変更しなかった。

## 損失・文脈診断

1,000の会話NLLは0.938816068889→0.938914025588と微悪化、5,000では0.925427100593→0.918060302769へ改善。1,000のTRAIN64利得微増はpool重複7例に集中し、他57例は微減。最終selectedでは全64のgain0.119447590783→0.139376357198、pool重複7例0.201071943556→0.220526422773、他57例0.109423547460→0.129410559671。pool全1024 gain0.196030869382→0.231562946225、正のgain944→967。どちらの群もTRAINで、57例をheldoutとはしない。全poolの意味読解をしたという主張もしない。

会話TRAIN99 sampleは0.887947724282→0.877600313657、DEVとの差は0.029747672767→0.030835749789。TRAIN全体平均ではなく、内容/長さ/話題を対応させた群でもない。gapの微増だけで過学習と断定しない。旧canonical差の診断やR25を旧値にするsequence saturation診断を、このR44対照の全TRAIN比較と混同しない。

正例15,720,338 targets/54,747,251bytes、80,000 row drawsと最終Python/Torch RNGはR44に完全一致。異なるのは固定LRの更新幅とそれによるmodel生成負例/勾配。自己負例1,000calls/32,280tokens/11,643negative positions。380callsが64上限、453callsにはnegative positionsがなかった。上限到達は長い失敗の一因候補だが、R30で128へ延長した旧試行は意味改善に失敗しており、自動的な解決とはしない。今回のnegative採点診断でもcap/zero-gradientで全損失が止まっている証拠はない。

主samplingの実10,000で57,089/189,166 index rowsを引いた。view/windowの内容は重複し、親が読んだ可能性もあるため、未抽出を未見と呼ばず、追加doseが有効とも断定しない。loss CSVは100更新ごとの1mini-batchの値で、全TRAIN平均ではない。今回は係数はR44と同じでLRだけ異なるが、自己負例は同一文章ではない。

## 原因の切り分けと次案

容量: 全4,655,808paramを固定した今回、会話NLLと一部短い自然応答が改善したため、直ちに大規模化だけを選ぶ根拠はない。小容量の限界は否定できない。

データ: 会話比40%/5%と原文を固定して得た差であり、新資料の効果ではない。なお、generic相槌や行政語調への転換が多く、語彙/ジャンルや文脈から応答を学ぶ目的関数の偏りは候補。新資料を入れる場合も別の1条件のroundとして利用条件と分割を確認する。

token/境界: own BPE40/30/30を固定。valid UTF8や同じ数値経路でも語片・修飾の崩れは残るため、文字の不正だけでは説明できない。token分割が原因でないと断定もしない。

LR/optimizer: 対応する親のmoments/counter/RNG、全100保存endpointの固定LR、有限性を確認。高LRで会話NLLは伸びたが共通DEVは悪化し、日常loopも悪化したため、汎用的な優越性は主張しない。R46を正式採用せず、会話改善が観測された研究用対照として次の一条件を切り分ける。

長さ/訓練量: context256の範囲内でも短い疑問や理由節が崩れる。長い自己生成の抑制horizon64と生成評価192の差は残るが、短い失敗全てを長さで説明しない。実10,000後も未熟という事実だけで単純追加doseを選ばない。

次は**R46を科学対照にsequenceUnlikelihood.coefficientだけ0.1→0.2**。LR0.000045、correct-context CE0.1、horizon64、データ/8層192/seed/R28初期fullstate/10,000dose/selector/gatesを全て維持する。反復負例の勾配は存在するため、その重みを一条件で試す。R45の正文脈CE係数増とは別目的で、R30のhorizon延長を無根拠に再実行もしない。改善を保証せず、NLL悪化や意味の劣化も同じ条件で記録する。次案の実更新はこの記録時点0。

## 数値・実行不備の開示

新84出力はPython/JavaScriptとrawFP32/7桁exportの全列が84/84一致。参照logit最大誤差は1.239776611328125e-05/2.193450927734375e-05、許容2e-4は維持。参照logitは一部位置であり全hardware保証ではない。旧selected JS42/raw25、旧original17のraw再計測はなく、旧terminalはSHA検証した歴史的証拠。既知R10 near-tie16/17分岐は修正せず保持。

学習後、追加したcompare_losses.pyが100-update eventsにもlearningRateを必須と誤認してKeyErrorで停止し、元pipeline exit1となった。実学習は10,000/Adam30000で完了済み。元430入力と元失敗ログを変更せず、compare_losses_recovered.pyでLR記録のある20validation eventsと100checkpoint監査を照合し、80件の欠損を補完せず別記した。続きの評価のみ再開し、dependent terminal診断も必要なprimary出力が揃ってから再実行。重み/optimizerへの追加更新0、terminal SHA不変、全評価復旧exit0。posttraining-recovery.jsonに経緯とSHAを保存。

作業中、単一行JSONの旧policyを広く表示する操作があり、TEST prefix metadataが表示対象に含まれ得た。訓練完了後で、出力は途中省略されたが、人手未見TESTとの主張を行わない。TEST生成/訓練投入/選択はしていない。posttraining-policy-display-incident.jsonに保存し、R39等の既知露出も消さない。以後policyは必要なJSON keyだけを読む。

生生成JSON/文字列は全て無修正。1,000のMarkdownだけ、最後のcode fence後の改行1byteを整え、before/afterと生JSON SHAを別記した。文章の修正や生成の切取りではない。外部重み/tokenizer/生成API/他モデルの生成正解/検索回答は使用しない。

再現状態はinitial/200/1,000/5,000/selected9,500/terminal10,000の6 aligned fullstates・optimizer/RNG・lossless parts、policy/source SHA、loss推移と全生成に保存。採用済み重みはR25のまま。容量対策で旧R45/R42の再構成可能raw重複を回収し、全Git原本/履歴を保持した。Git packも全checksum検証後に既にpackされたloose重複だけを除いた。
