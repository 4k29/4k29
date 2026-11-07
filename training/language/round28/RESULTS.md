# round28 結果 — 実学習と無加工全文の検証

Round28 sibling of adopted Round25: ONLY human everyday-conversation corpus mass0→0.30; old masses×0.70, all model/objective/LR/seed fixed

実optimizer更新 **10000/10000**、counter [20000]。選択step 10000、best exposed-DEV CE NLL/byte **0.971898957126619**、事前対照閾値 0.971422085238788。生成の見た目をstep選択へ使用しない。

| 同入力・同生成条件DEV17件 | round25 | round28 |
|---|---:|---:|
| 初文成立 | 8 | 7 |
| 非長期ループ | 4 | 6 |
| 全文意味成立 | 0 | 0 |
| 全厳格言語ゲート | False | False |

人間会話DEV NLLは約28%改善したが共通DEV NLLは0.9714220852→0.9718989571と悪化し、初文8→7、全文意味0→0。日常会話12件も全文0のままで長期ループ11→12、EOS1→0。固定Paretoと追加実用ガードに不合格のため採用せず最後の採用Round25を保持する。語調と尤度の学習を文脈に沿う意味改善とは認定しない。

事後4gram反復率 63.940760%→57.814710%。EOS 2→5。全token/全文完全同一 0/17。反復率・短さ・EOSを意味成立と同一視しない。

## 固定条件と再現

対照の選択step 9500、新モデルの選択step 10000。両方とも同じ最小DEV CEの選択手順を使う。選択stepが異なる場合、生成差には選択された更新段階の影響も含まれる。

設定 {'vocabulary': 5455, 'dim': 192, 'layers': 8, 'heads': 4, 'hidden': 768, 'context': 256, 'dropout': 0.1, 'epsilon': 1e-05}、parameters 4655808。独自weights/独自BPE語彙のみ、通常40%/glyph30%/random-character-cuts30%、CPU2/FP32/batch8/seed系譜2049、LR2.2499999999999998e-5、wd.05、clip1、検証500更新。policy.jsonとsource-manifest.jsonにコード・データ・原文・利用条件・親checkpointのSHAを結合。

同じRound11 latestの整合model/optimizer/Torch RNG/private Python RNGを復元する単独要因の兄弟比較。前ラウンドselected weightsへlatest optimizerを混ぜない。各ラウンド10000更新を累積weight系譜へ単純加算しない。容量を変えた場合は旧座標/新座標の系譜とtensor counterを別記する。

実人間原文target 15,548,462token / 54,265,757bytes、elapsed 9155.51秒。CE DEV選択指標とtrain合成目的を分け、loss-history.csv、training-loss-events.csv、paired-ce-curve.csvを保存。objective-audit.jsonの記録点 100。自己生成がある場合のtoken/負例数は人間原文exposureへ含めない。学習中の書き出しは毎回異なるため、その反復位置の集計を固定入力の旧新評価と同一視しない。

checkpoint-0.ptとcheckpoint.ptにmodel/AdamW/全RNG/実step/historyを保存、selected-weights.ptとmodel.jsはbeststate。大容量checkpointを分割保存する場合はSHA付きchunksとbitexact再構築を別記する。完了済みrunを再実行せず、未完了かつ稼働なしだけrun.sh --resume。persistent controllerがチャット接続と独立に学習・機械評価・PR保存を行う。mechanical pendingは当時のsnapshotで、本報告の最終読解が後に追加された。

## 生成・評価・数値差

FULL_GENERATIONS.mdとold/new-validation.jsonに全prefix・全token・無加工全文。greedy full vocabulary/max192/trueEOS/Python1thread固定、推論penalty/文章修正/検索/テンプレートなし。全17prefix+continuationをassistantが実読解し、理由とSHAをnew-manual.jsonに保存。独立盲検の人間採点ではない。従来の初文80%/非長期ループ90%/全文意味80%を全scope/groupで要求し緩和しない。未知固有名や仕様の真偽未確認だけで言語失敗とせず、事実正確性も認定しない。感度分析はevaluation-sensitivity.json。

17件は露出済みDEVで新TESTではない。予約データをencode/loss/生成に使用せず、未見一般化は未証明。新しいコーパスのfold/重複監査・reserved保護はsource policyに従う。短い/近似重複なしの保証はしない。

Python/JS完全列は旧17/17・新17/17、reference最大絶対差は旧1.04904174805e-05・新9.53674316406e-06、許容2e-4不変。rawFP32対7桁export 17/17。numerical-divergence.jsonに実分岐と既知Round10の16/17 near-tieを保存し、全入力への一致保証はしない。

## 原因の切り分け

- 容量: 単独の容量比較でない限り不足を確定しない。主述の短距離崩壊もありcontext延長のみで解決とは断定しない。
- データ: 政府・専門文と古い物語に偏り、露出済みDEVの改善は未見一般化ではない。原文追加条件は他要因と分離して評価する。
- 分割: 同一独自語彙/40-30-30を維持。token4gramと意味反復は一致しない。generation-granularity.jsonを保存。
- optimizer/LR: 親整合状態と既存terminalLRを固定。追加目的が有用な反復を抑える可能性もあり、CE悪化を隠さない。
- 学習不足/過学習: 旧固定canonical TRAIN 0.773372203、DEV 1.005381362、gap 0.232009160。全拡張TRAINを代表せず、この診断だけで単純延長を決めない。
- 数値誤差: 実列が一致しても意味が破綻するなら数値差のみでは説明できない。丸め・言語間near-tieを区別する。
- 評価: 1seed/17既存DEV/assistant読解の限界。全文・個別理由・曖昧な解釈を残す。複数重要条件を同一ラウンドで切り替えない。

## 個別全文評価

- **validation-aozora-00**: 初文ののぼりはじめましたは自然。後続はおい・おじさん・おじいちゃんの呼びかけと所有句の長い反復で展開しない。
- **validation-aozora-01**: 寒さを防ぐために出来るで文が終わり、できる対象やことが欠ける。その後は大量の全角空白で上限に達する。空白も原文のまま保存した。
- **validation-aozora-02**: 葦が風のなかにかけて来たのでございましたは駆けて来たと解釈でき、擬人化も物語として許容し初文9点。後続はもう一度もや母と顔の所有関係を長く反復する。初文の曖昧さは感度分析に残す。
- **validation-mic-03**: 引用が閉じずInteration/Internationに類する文字列を長く反復する。未知の英字名自体を失敗理由とはしない。
- **validation-mic-04**: 初文の市場規模は自然。後続は団体数を兆億円で表す数量関係の崩れとテレワーク導入の局所反復。金額が変化する有限の列挙として旧基準同様に長い周期ループとは区別するが全文意味は不成立。
- **validation-env-05**: 初文から産業創出を図るとともにを重ねる。後続も産業産業やCO2所有関係が崩れ引用が閉じない。変化する局所反復としてprimaryでは長期周期ループに数えない。
- **validation-env-06**: 海洋ごみの地方公共団体が設置など格と修飾が崩れ、法律名や施行の節を連ねたまま閉じない。反復はあるが法律名が変わり同節の反復も有限でありprimaryでは長期周期ループと区別する。
- **validation-jma-07**: お知らせするという活用は改善したが、噴火速報はという主題がご覧くださいへ流れて主述が対応しない。対象と条件の局所反復があり全文の説明は成立しない。
- **validation-jma-08**: 解析雨量はという説明の主題と条件がについて教えてくださいへ流れ、詳しくは解説をご覧くださいへ発話目的も変わる。短くEOSで終わるが全文意味成立とはしない。省略された対話を補う解釈は感度分析に分離。
- **validation-mdn-new-00**: 初文はCSSで使用するSVGプロパティを指定することができますで言語として自然。後続はSVGプロパティを同じ節で長く反復する。API事実の正確性は認定しない。
- **validation-mdn-new-01**: 初文はグローバル属性を指定することができますで自然。後続は要素の修飾節が長く再帰する。
- **validation-mdn-new-02**: 初文はメソッドがオブジェクトのメソッドを返すという言語的関係として成立可能で9点。未知名のみで失敗としない。後続はNode等へ飛び大量のピリオドに崩壊する。
- **validation-mdn-new-03**: 初文はポリシーオブジェクトを用いてSVGリクエストを提供するという文として成立可能で9点。後続の提供・取得の修飾句が長く入れ子になり展開しない。事実正確性は別問題。
- **validation-stat-new-00**: 提供する方法を提供するという修飾が三重に再帰して何を説明するか曖昧になる。短い一文でEOSとなる有限の局所反復として長期ループとは区別するが、初文と全文意味は不合格。
- **validation-stat-new-01**: 客観的なの修飾先が取組になりデータとの関係が弱い初文8点。後続はデータを使っての長い反復。
- **validation-bunka-new-00**: 表彰や協力覚書を開催するという目的語・述語の関係が不自然でアジア等も反復する。後続は日や句点の長い崩壊。
- **validation-bunka-new-01**: 必要な施策を講じられていますは目的格と受動の関係が不自然で初文7点。敬語の省略主語と解釈する代替は感度分析に残す。後続は法律名と地方公共団体を長く反復。

## 日常会話に関する実測と次の仮説

同じ人間会話DEV99ファイル（98 unique、66402 targets/247408 bytes/390 windows）のcanonical NLLは **1.288001013127 → 0.928190407797**（27.94%低下）。これは既存DEV診断であり新TESTではない。固定128 TRAIN会話の3分割viewサンプルは **1.286866583640 → 0.904329643402**。TRAINサンプルとcanonical DEVは分割・窓の集計が異なるため、この差をそのまま汎化gapとはしない。

一方、固定の日常12件は全文意味 **0→0**、長期loop **11→12**、EOS **1→0**。新出力は「そうなんですね」「食べたいですね」など会話的な語調を学んだが、問いへの応答・意味の展開が続かない。12件の無加工全文はexecution/DAILY_FULL_GENERATIONS.md、個別の実読解はdaily-new-reading.jsonに保存。Python/JSは旧新とも12/12、rawFP32/7桁exportも旧新とも12/12。数値一致は意味成立を保証しない。

8975 TRAIN対話には269877発話があるがEOSは対話末の8975個のみ（発話数の約3.33%）。発話終端の学習が疎である可能性はある。ただし独自BPEには改行をまたぐpieceがあり、発話末EOS挿入はtoken分割も変えうるため、単純な終了記号だけの効果とは断定できない。

次の単一条件候補は、同じ原文・分割・モデルの人間会話混合率を30%から10%へ変更する用量比較。科学的採用基準は最後の採用Round25を維持し、Round28との比率差も明示する。30%で共通DEVと日常非loopが悪化したため、会話NLL向上と既存言語保持の両立を検証する合理性がある。語彙、容量、LR、EOS表現、推論設定は同時に変更しない。改善がなければ比率の微調整を盲目的に繰り返さず、発話境界と文脈対応の学習構造を次の独立実験で検討する。

Round27の容量増加で意味改善がなく、Round28のデータ追加で会話尤度のみ大きく改善したため、容量不足だけでは説明できない。局所の主述・格関係も壊れるのでcontext長だけの不足とも言えない。固定LR一条件からoptimizer原因や過学習を確定しない。元の人間会話を忠実に予測するteacher-forcingと、自分の誤りを入力に含む自由生成の差が残る。自己生成反復目的も維持したが解消していない。新しい保持TESTによる一般化は未証明。
