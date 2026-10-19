# round27 結果 — 実学習と無加工全文の検証

Round27 sibling of round25: ONLY FFN hidden768→1536 with exact old function/coordinate moments and own new zero-output features; all adopted data/objective/LR fixed

実optimizer更新 **10000/10000**、counter [20000]。選択step 9500、best exposed-DEV CE NLL/byte **0.971349132914315**、事前対照閾値 0.971422085238788。生成の見た目をstep選択へ使用しない。

| 同入力・同生成条件DEV17件 | round25 | round27 |
|---|---:|---:|
| 初文成立 | 8 | 8 |
| 非長期ループ | 4 | 4 |
| 全文意味成立 | 0 | 0 |
| 全厳格言語ゲート | False | False |

主判定は初文8→8/非長期ループ4→4/全文意味0→0、共通NLLは0.9714220852→0.9713491329と僅かに改善し、固定ParetoのNLL-only保持は選択可能。ただし保持は必須ではない。容量を約50.6%増やしても全文と日常12件は0のまま、人間会話DEV NLLは1.2880010131→1.2896154406と微悪化。局所反復や省略の境界解釈でも言語改善を確証できない。日常会話という事前の実用目標とambiguousInterpretationCanBlockAdoption/May retain条項に基づき、容量設定を次の標準として採用せず結果を保存する。これは主判定のPareto不合格という意味ではなく、任意のNLL-only採用を保留した判断。次の人間会話TRAIN追加は最後の採用Round25設定から別roundで比較する。

事後4gram反復率 63.940760%→60.252264%。EOS 2→3。全token/全文完全同一 2/17。反復率・短さ・EOSを意味成立と同一視しない。

## 固定条件と再現

対照の選択step 9500、新モデルの選択step 9500。両方とも同じ最小DEV CEの選択手順を使う。選択stepが異なる場合、生成差には選択された更新段階の影響も含まれる。

設定 {'vocabulary': 5455, 'dim': 192, 'layers': 8, 'heads': 4, 'hidden': 1536, 'context': 256, 'dropout': 0.1, 'epsilon': 1e-05}、parameters 7021248。独自weights/独自BPE語彙のみ、通常40%/glyph30%/random-character-cuts30%、CPU2/FP32/batch8/seed系譜2049、LR2.2499999999999998e-5、wd.05、clip1、検証500更新。policy.jsonとsource-manifest.jsonにコード・データ・原文・利用条件・親checkpointのSHAを結合。

同じRound11 latestの整合model/optimizer/Torch RNG/private Python RNGを復元する単独要因の兄弟比較。前ラウンドselected weightsへlatest optimizerを混ぜない。各ラウンド10000更新を累積weight系譜へ単純加算しない。容量を変えた場合は旧座標/新座標の系譜とtensor counterを別記する。

実人間原文target 15,543,567token / 54,500,806bytes、elapsed 12262.04秒。CE DEV選択指標とtrain合成目的を分け、loss-history.csv、training-loss-events.csv、paired-ce-curve.csvを保存。objective-audit.jsonの記録点 100。自己生成がある場合のtoken/負例数は人間原文exposureへ含めない。学習中の書き出しは毎回異なるため、その反復位置の集計を固定入力の旧新評価と同一視しない。

checkpoint-0.ptとcheckpoint.ptにmodel/AdamW/全RNG/実step/historyを保存、selected-weights.ptとmodel.jsはbeststate。大容量checkpointを分割保存する場合はSHA付きchunksとbitexact再構築を別記する。完了済みrunを再実行せず、未完了かつ稼働なしだけrun.sh --resume。persistent controllerがチャット接続と独立に学習・機械評価・PR保存を行う。mechanical pendingは当時のsnapshotで、本報告の最終読解が後に追加された。

## 生成・評価・数値差

FULL_GENERATIONS.mdとold/new-validation.jsonに全prefix・全token・無加工全文。greedy full vocabulary/max192/trueEOS/Python1thread固定、推論penalty/文章修正/検索/テンプレートなし。全17prefix+continuationをassistantが実読解し、理由とSHAをnew-manual.jsonに保存。独立盲検の人間採点ではない。従来の初文80%/非長期ループ90%/全文意味80%を全scope/groupで要求し緩和しない。未知固有名や仕様の真偽未確認だけで言語失敗とせず、事実正確性も認定しない。感度分析はevaluation-sensitivity.json。

17件は露出済みDEVで新TESTではない。予約データをencode/loss/生成に使用せず、未見一般化は未証明。新しいコーパスのfold/重複監査・reserved保護はsource policyに従う。短い/近似重複なしの保証はしない。

Python/JS完全列は旧17/17・新17/17、reference最大絶対差は旧1.04904174805e-05・新1.04904174805e-05、許容2e-4不変。rawFP32対7桁export 17/17。numerical-divergence.jsonに実分岐と既知Round10の16/17 near-tieを保存し、全入力への一致保証はしない。

## 原因の切り分け

- 容量: 単独の容量比較でない限り不足を確定しない。主述の短距離崩壊もありcontext延長のみで解決とは断定しない。
- データ: 政府・専門文と古い物語に偏り、露出済みDEVの改善は未見一般化ではない。原文追加条件は他要因と分離して評価する。
- 分割: 同一独自語彙/40-30-30を維持。token4gramと意味反復は一致しない。generation-granularity.jsonを保存。
- optimizer/LR: 親整合状態と既存terminalLRを固定。追加目的が有用な反復を抑える可能性もあり、CE悪化を隠さない。
- 学習不足/過学習: 旧固定canonical TRAIN 0.754359563、DEV 1.009768001、gap 0.255408438。全拡張TRAINを代表せず、この診断だけで単純延長を決めない。
- 数値誤差: 実列が一致しても意味が破綻するなら数値差のみでは説明できない。丸め・言語間near-tieを区別する。
- 評価: 1seed/17既存DEV/assistant読解の限界。全文・個別理由・曖昧な解釈を残す。複数重要条件を同一ラウンドで切り替えない。

## 個別全文評価

- **validation-aozora-00**: 初文ののぼりはじめましたは自然。後続の呼びかけと祖父の所有句は長く再帰し、会話が進まない。
- **validation-aozora-01**: 寒さを防ぐために出て来たという初文は旧と同じ。出る先を外気と決めつけず、成立可能な省略として旧の9点を保持。全文は夜の所有句の長いループ。
- **validation-aozora-02**: 葦が風のなかにかけていたの対象が不明で、おかあさんがを重ねる初文は成立しない。母親と顔の所有・目的語が長く再帰する。擬人化自体は失敗理由でない。
- **validation-mic-03**: 未知英字名ではなく引用と文が閉じずInternationを長く反復する点で失敗。
- **validation-mic-04**: 市場規模の初文は自然。後続は情報化投資の種類を局所反復し、ソフトウェアを占めているやマイナンバーカード増の億円など対象・数量関係が崩れる。全文には金額・年度が変化するため、旧の局所反復と同じくprimaryでは長い周期ループとは区別。境界例として感度分析も保存。
- **validation-env-05**: 初文の地方公共団体等と連携しつつが3回重なるため旧同様の失格。後続の法律・脱炭素化促進の入れ子も意味の進行が乏しく最後も途中。旧と同じ局所再帰としてprimaryでは長期ループと区別。
- **validation-env-06**: 新出力は図りますで初文が閉じるが、海洋ごみを整備・実施するという目的語と述語の関係が崩れ海域の所有句を繰り返す。後続も海洋ごみを海洋ごみに調査、未完引用へ崩れる。EOS自体で合格にはしない。
- **validation-jma-07**: 初文のお知らせるという旧の活用崩れが解消し、噴火の発生を知らせて発表する文として成立する。速報と警報の仕様の真偽は認定しない。後続は発生に及びゆるを要予想の語形成崩れ、防災対応の局所反復で説明が破綻。旧と同じく複数の説明句は変化するためprimaryでは長期周期ループと区別し、厳しい反復解釈を別記。
- **validation-jma-08**: 少雨が予測をきる必要がありますという活用・目的語・主述の初文が成立しない。後続も基準値の自己説明や解説をご覧くださいの局所重複はあるが文は変化し、旧と同じく長期同一周期ループと区別。全文意味は成立しない。
- **validation-mdn-new-00**: CSSパスをfalseに設定する初文は旧同様に文法上成立。APIの正誤は認定しない。後続はfont-fillの値が指定された場合の長い未完ループ。
- **validation-mdn-new-01**: 初文のグローバル属性を指定しますは自然。後続は要素を指定する要素、設定されている要素の長い再帰で対象を失う。EOSでも全文意味不成立。未知の要素名自体は失敗理由でない。
- **validation-mdn-new-02**: メソッドがInternationオブジェクトを返す初文は旧と同じ9点。後続は返却句から配列の長いループへ崩れる。未知名を事実認定しない。
- **validation-mdn-new-03**: ポリシーオブジェクトを使用してJavaScriptでSVGオブジェクトを参照する初文は、二重目的語なしで文法上成立。APIの真偽は認定しない。後続はSVGリクエストを送信するの多重再帰が長く続き最後も未完。
- **validation-stat-new-00**: ウェブサイトの所有句からHTML文書の読み込みを提供するという対象関係に崩れる。続くこの例ではから始まるHTML要素の長い再帰で統計文脈を保たない。EOSで終わっても不合格。
- **validation-stat-new-01**: データなどの客観的な取組という初文の不自然な修飾は旧と同じ。後続は取組を進める自己説明から製品・サービスの所有句を長く繰り返して意味が進まない。
- **validation-bunka-new-00**: 初文は文法的だが国際連携の下を重ね協力関係者の協力を強化すると冗長に続く。旧の同種の目的・対象の弱さと同じ8点を保持。後続の国際協力句は国の長い連続へ崩れる。人物名や史実の未確認だけの失格でない。
- **validation-bunka-new-01**: 必要な施策を講じられていますという初文は受動なら施策がとの格関係を欠き、明示しない人物への尊敬と読む余地は別記する。後続は施設・法律・認定・地域計画を重ねる長い再帰と地方公共団体が認定される事業者などの関係不明瞭さで全文不成立。

## FFN capacity and checkpoint lineage

Only FFN hidden768→1536 changes; depth8/embedding192/heads4/context256 and all own data/tokenizer/objective/LR stay fixed. Old coordinates start at49000 lineage updates; new coordinates start at0. New moment coordinates are zero but inherit global AdamW tensor age10000, not independent fresh bias correction. Full latest and zero-update checkpoints are stored as lossless SHA-bound40MiB chunks; reconstruct exact bytes before resume. Additional everyday DEV uses the identical fixed12 openings and humanDEV99 targets; no new TEST or relaxed gate.

## 日常会話を中心にした判定と次の条件

| 追加露出DEV（TESTではない） | Round25 | Round27 |
|---|---:|---:|
| 日常12件・全文意味成立 | 0 | 0 |
| 日常12件・長期ループ | 11 | 11 |
| 日常12件・EOS | 1 | 1 |
| 人間会話99ファイル canonical NLL/byte | 1.2880010131269757 | 1.289615440610918 |

日常12件の全文を実読解しdaily-new-reading.jsonに理由を保存した。夕食の短いEOS出力は旧と全文同一で「食中毒の原因を食べる」「食べるのは大量です」という意味破綻がある。他の会話は待ち合わせ・疲れ・料理・近況への返答にならず、古風な所有句や教師・家族・教室への逸脱と長い反復が残る。DAILY_FULL_GENERATIONS.mdに無加工全文、対応JSONに全tokenを保存。日常12件でもPython/JSは旧新12/12、rawFP32/7桁exportも旧新12/12。既知の過去のnear-tie分岐を消していない。

人間会話99は99ファイルであり、1組の完全重複を含む98独立内容である。固定99ファイル測定は変更せず、この制約を報告する。dialogueIdが重複するため次のデータはsourcePathとSHAで識別する。NLLの分母は247408 serializedUTF8bytes、66402targets/390windowsで旧新一致。混合文書DEVと絶対値を直接比較しない。

これは同一データ・サンプル列・最終Python/Torch RNG・実15543567targets/54500806bytesで容量だけを変えた比較である。追加約50.6%パラメータでも共通NLL改善は約0.0075%に留まり、初文は噴火速報の活用が直る一方で施策を講じられていますが崩れ、全体8→8。全文0→0、日常0→0、人間会話NLL微悪化。実所要は旧9633.62秒、新12262.04秒（検証を含み負荷条件を統制した速度試験ではない）。現在のデータと目的におけるFFN不足が支配的原因という仮説は支持されない。depth/埋め込み/文脈長の効果まで否定する結果ではない。

主判定は固定ParetoのNLL-only保持を選択できる状態であり、Pareto不合格だったと偽らない。同方針のMay retainは保持を義務づけない。実用目標の日常会話が改善せず、追加容量の根拠が弱く、局所反復と省略の解釈差もあるため、その任意保持を行わない。より許容的な尊敬表現の読みでは初文9件になる感度分析も保存したが、全解釈で厳格ゲートは不合格。主判定の閾値を緩めたわけではない。

旧TRAIN限定gap0.2554084376は分布差も含む。短い主述の崩れと日常入力+生成がcontext256以内であること、UTF8入力境界と数値一致の検証から、文脈長や推論丸めだけが主因とは考えにくい。optimizer/勾配/実カウンタの不整合も監査で認めない。LRと全体学習量は未分離であり、単純な増大・更新延長に飛びつかない。次はRound25のモデル・目的・LRを保持して、人間の日常会話TRAINの混合だけを変更する。原文の短文・応答・話題継続をモデルが学べるかを実測し、反復抑制やNLL改善を意味獲得と混同しない。
