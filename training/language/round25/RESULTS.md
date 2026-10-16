# round25 結果 — 実学習と無加工全文の検証

Round25 sibling of adopted experimental Round24: add coefficient0.1 self-generated repeated-fourgram negative-only sequence loss every10optimizerupdates; no other learning factor changed

実optimizer更新 **10000/10000**、counter [20000]。選択step 9500、best exposed-DEV CE NLL/byte **0.971422085238788**、事前対照閾値 0.971423106158840。生成の見た目をstep選択へ使用しない。

| 同入力・同生成条件DEV17件 | round24 | round25 |
|---|---:|---:|
| 初文成立 | 7 | 8 |
| 非長期ループ | 4 | 4 |
| 全文意味成立 | 0 | 0 |
| 全厳格言語ゲート | False | False |

Retain sequence UL addition only as controlled experimental baseline: official first counts7→8, nonloop4→4, fullmeaning0→0, NLL lower by only1.02092e-6 (~0.000105%). Raw4gram repetition64.8552%→63.9408%. The duplicate object in mdn03 first clause is repaired by the model itself, but its continuation loops. No natural full-Japanese, robust NLL, or unseen-generalization success established. Same fixed rubric and strict public gates remain unchanged.

事後4gram反復率 64.855190%→63.940760%。EOS 4→2。全token/全文完全同一 8/17。反復率・短さ・EOSを意味成立と同一視しない。

## 固定条件と再現

対照の選択step 9500、新モデルの選択step 9500。両方とも同じ最小DEV CEの選択手順を使う。選択stepが異なる場合、生成差には選択された更新段階の影響も含まれる。

設定 {'vocabulary': 5455, 'dim': 192, 'layers': 8, 'heads': 4, 'hidden': 768, 'context': 256, 'dropout': 0.1, 'epsilon': 1e-05}、parameters 4655808。独自weights/独自BPE語彙のみ、通常40%/glyph30%/random-character-cuts30%、CPU2/FP32/batch8/seed系譜2049、LR2.2499999999999998e-5、wd.05、clip1、検証500更新。policy.jsonとsource-manifest.jsonにコード・データ・原文・利用条件・親checkpointのSHAを結合。

同じRound11 latestの整合model/optimizer/Torch RNG/private Python RNGを復元する単独要因の兄弟比較。前ラウンドselected weightsへlatest optimizerを混ぜない。各ラウンド10000更新を累積weight系譜へ単純加算しない。容量を変えた場合は旧座標/新座標の系譜とtensor counterを別記する。

実人間原文target 15,543,567token / 54,500,806bytes、elapsed 9633.62秒。CE DEV選択指標とtrain合成目的を分け、loss-history.csv、training-loss-events.csv、paired-ce-curve.csvを保存。objective-audit.jsonの記録点 100。自己生成がある場合のtoken/負例数は人間原文exposureへ含めない。学習中の書き出しは毎回異なるため、その反復位置の集計を固定入力の旧新評価と同一視しない。

checkpoint-0.ptとcheckpoint.ptにmodel/AdamW/全RNG/実step/historyを保存、selected-weights.ptとmodel.jsはbeststate。大容量checkpointを分割保存する場合はSHA付きchunksとbitexact再構築を別記する。完了済みrunを再実行せず、未完了かつ稼働なしだけrun.sh --resume。persistent controllerがチャット接続と独立に学習・機械評価・PR保存を行う。mechanical pendingは当時のsnapshotで、本報告の最終読解が後に追加された。

## 生成・評価・数値差

FULL_GENERATIONS.mdとold/new-validation.jsonに全prefix・全token・無加工全文。greedy full vocabulary/max192/trueEOS/Python1thread固定、推論penalty/文章修正/検索/テンプレートなし。全17prefix+continuationをassistantが実読解し、理由とSHAをnew-manual.jsonに保存。独立盲検の人間採点ではない。従来の初文80%/非長期ループ90%/全文意味80%を全scope/groupで要求し緩和しない。未知固有名や仕様の真偽未確認だけで言語失敗とせず、事実正確性も認定しない。感度分析はevaluation-sensitivity.json。

17件は露出済みDEVで新TESTではない。予約データをencode/loss/生成に使用せず、未見一般化は未証明。新しいコーパスのfold/重複監査・reserved保護はsource policyに従う。短い/近似重複なしの保証はしない。

Python/JS完全列は旧17/17・新17/17、reference最大絶対差は旧1.14440917969e-05・新1.04904174805e-05、許容2e-4不変。rawFP32対7桁export 17/17。numerical-divergence.jsonに実分岐と既知Round10の16/17 near-tieを保存し、全入力への一致保証はしない。

## 原因の切り分け

- 容量: 単独の容量比較でない限り不足を確定しない。主述の短距離崩壊もありcontext延長のみで解決とは断定しない。
- データ: 政府・専門文と古い物語に偏り、露出済みDEVの改善は未見一般化ではない。原文追加条件は他要因と分離して評価する。
- 分割: 同一独自語彙/40-30-30を維持。token4gramと意味反復は一致しない。generation-granularity.jsonを保存。
- optimizer/LR: 親整合状態と既存terminalLRを固定。追加目的が有用な反復を抑える可能性もあり、CE悪化を隠さない。
- 学習不足/過学習: 旧固定canonical TRAIN 0.754895754、DEV 1.009534028、gap 0.254638274。全拡張TRAINを代表せず、この診断だけで単純延長を決めない。
- 数値誤差: 実列が一致しても意味が破綻するなら数値差のみでは説明できない。丸め・言語間near-tieを区別する。
- 評価: 1seed/17既存DEV/assistant読解の限界。全文・個別理由・曖昧な解釈を残す。複数重要条件を同一ラウンドで切り替えない。

## 個別全文評価

- **validation-aozora-00**: 初文ののぼりはじめましたは自然。後続はおい・おじさんからおじいちゃんへ呼び名が変わるが、長い同じ呼びかけの反復が再開する。おじいちゃんのかいという不自然な接続と、最後の所有句の未完もあり、会話の意味は進まない。創作の人物が出ること自体を失敗理由にしない。
- **validation-aozora-01**: 寒さを防ぐために出て来たという初文は文法的には成立する。出る先が不明で目的との関係は弱いが、文脈にない外気へ出たと決めつけて失格にしない。後続はその夜の夜の夜を長く反復する。初文の接続には解釈差を別記する。
- **validation-aozora-02**: 初文の葦が風のなかにかけていたという対象不足と、おかあさんの主語・対象の重複は旧と同じ。後半の一部においでになったが入るが、母の所有・対象を長く再帰し関係が成立しない。擬人化のみの失格ではない。
- **validation-mic-03**: 立ち上げた名称の引用が閉じず、Internationを長く反復する。未知英字名の存在ではなく文の未成立と反復を失敗理由にする。
- **validation-mic-04**: 初文は自然。後続はコンテンツ市場の内訳から電話契約へ移り、契約数を億円や百分率で表す対象・単位関係が崩れる。局所的な内訳・電話句の再利用はあるが長い周期ループとはしない。EOSだけでは全文合格にしない。
- **validation-env-05**: 初文の地方公共団体等と連携しつつ三回反復と地域の地域は旧と同じ。後続も法律・促進・地域の関係を重ね、最後は地域の所有を四回重ねた途中で切れる。局所再帰は残るが、旧と同じく長い周期ループとは区別する。説明の対象と接続は成立しない。
- **validation-env-06**: 海洋ごみの所有を重ね、海洋ごみの維持と再生可能エネルギーを不自然に接続する。利用の促進からエネルギーの導入を六回長く重ね、海岸保全施設の説明が進まない。初文も閉じず、全文意味は不成立。
- **validation-jma-07**: お知らせる、予想される現象ののという初文の活用と修飾の崩れは残る。後続はとるべき防災対応を三回ずつ重ね、警報と警戒レベルの説明が接続しない。局所反復はあるが全文は変化し、旧と同様に長い同一周期ループとは区別。最後も引用途中で切れる。
- **validation-jma-08**: 解析雨量はという主題から発表状況や少雨が地上の大雨を把握できるという述語へ移り、主語と把握する主体が成立しない。後続も発表状降水帯、災害の危険度の高まりをご覧くださいという対象不足、雨域を予測した表面などで関係が崩れる。各文は変化し長い同一周期ループではないが、文間の説明は一貫しない。引用も最後まで閉じない。
- **validation-mdn-new-00**: 関数がCSSパスをfalseに設定する初文は文法上成立し、API仕様の真偽は認定しない。後続はfont-fillプロパティの値が指定された場合を長く反復して閉じない。
- **validation-mdn-new-01**: 初文のグローバル属性を指定しますは自然。後続は要素に設定されている要素という修飾を長く再帰して対象を失う。旧のEOSが今回はなくなるが、EOSの有無とは独立に長い再帰と意味の進行不足を失敗とする。未知の要素名だけを失敗理由にしない。
- **validation-mdn-new-02**: メソッドがInternationオブジェクトを返す初文の文法・接続は成立し、未知名の真偽は認定しない。後続からメモの重複は減るが、同じ配列の返却文を四回重ね、最後は配列の単語列へ長く崩れる。局所的な重複除去は全文意味の改善を示さない。
- **validation-mdn-new-03**: ユーザー定義のポリシーオブジェクトを使用してJavaScriptでSVGリクエストを送信する初文は、旧の目的語二重置きが解消し文法・対象関係が成立する。SVGリクエストや実際のAPI挙動の真偽は認定せず、未知用語のみでは失格にしない。後続はSVGリクエストを送信するを長く入れ子に反復して説明が進まず、最後もSVG SVGで切れ、全文意味は不成立。
- **validation-stat-new-00**: ウェブサイトの所有を重ねたうえでHTML要素を提供・指定する句を多重に再帰する。後続も同じこの例ではから始まる文を長く反復し、統計の文脈からHTMLへ崩れる。EOSでも全文不合格。
- **validation-stat-new-01**: データなどの客観的な取組という修飾関係は旧と同様に不自然。後続は具体的な取組の自己説明から製造業の創出・所有の長い反復へ崩れる。
- **validation-bunka-new-00**: 表彰のための国際連携の下から再び協力強化のための国際連携の下へ重ね、初文は文法的だが冗長で対象・目的が弱い。後続は日中韓・日米国の関係が崩れて韓国を長く反復する。歴史的事実の未確認だけの判定ではない。
- **validation-bunka-new-01**: 必要な施策を講じますという初文は旧と同じく自然。後続は文化観光から対象物質の整備、事業者の整備、地方公共団体の整備へ対象が崩れ、地域計画の整備を十数回長く繰り返す。法の事実未確認とは別に、対象関係と説明の進行が成立しない。
