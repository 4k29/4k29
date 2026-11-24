# 日本語データ基盤：取得・実装・監査と学習判断

**候補原文の取得、実データのパイプライン実行、評価基盤、次期比較schedule、実モデルのゼロ更新監査を完了した。本学習はNo-Go。** 新しいoptimizer更新、Tokenizer fit、公開モデル変更、有料GPU、マージは0。自然な対話能力が改善したと主張する実験ではない。

## 実際に取得・保存した量

| 原典 | 固定版・利用条件 | 重複処理後の候補本文tokens（現行独自BPE） |
|---|---|---:|
| JaQuAD upstream TRAIN 30shards | HF revision05600ff…、CC BY-SA3.0。691記事/9713contexts/31,748人手QA | 3,306,221 |
| 日本語Wikibooks公式dump | 20261001、公式rights API/規約のCC BY-SA4.0 | 19,183,448 |
| 日本語Wikivoyage公式dump | 20261001、公式rights API/規約のCC BY-SA4.0 | 861,589 |
| **計** | **20,002派生文書。全て未採用candidate** | **23,351,258** |

取得payloadは58,973,860bytes、永続保存用raw archiveは41,352,653bytes。公式Wiki size/SHA1、自前SHA256、全30shardのSHAを照合した。原文、出典URL、版、article/history URL、license、contributor情報、加工条件を保存。既存RP/JMRDを新規取得量へ加算していない。本文token数にQAの重複contextや回答spanを水増ししていない。

**10–30Mという候補量は確保できたが、10–30Mの「品質・人間原文性を確認済みの新規TRAIN」を確保したとは言えない。** JaQuADの人手QAという出版社の説明と、Wikipedia本文の全執筆過程は別である。両Wikiのbot/LLM混入・第三者引用・古文・コード等も未確定。pre2022最新revisionかつ最終contributor名にbotを含まないTRAIN部分は816,149tokensだが、これも人間のみの証明ではない。licenseを確認したことだけで全文章を採用していない。詳細はSOURCES.md/catalog.json/DATA-LICENSE.md。

将来100M以上へ拡張する公式日本語Wikipedia dumpのmetadataは確認したが、本体約4.879GBは未取得。政府の生活ガイド候補は403/404で取得できず、政府公開＝無条件利用可とは判断していない。100Mを取得済み/人間原文性確認済みと記録しない。

## 実装・実行した処理

rawと派生本文を分離し、派生正規化はNFCと改行統一。NFKC、意味の言い換え、LLM修正をしていない。Wikiは固定MIT parserでtemplate/code/math/table/media等を除外し、削除統計・元wikitext SHAを保持する。見出し・リスト・古語等が完全に消えたわけではない。

raw exact3343、NFC/空白canonical追加96、検証済みnear696段落を候補本文から除外した。近重複はcharacter5gram候補検索後Jaccard>=.85を検証し、293,758比較/2657near pairs。頻出postingを53,954回skipしたため、完全な近重複/意味family監査とは言わない。既存RP187,667発話との段落丸ごとcanonical一致0も、部分転載や意味独立性の証明ではない。

同じ記事・book chapter・exact/near関係をunionしてからsplitした。品質読解で、`刑事訴訟法第…条`等を別文書familyにしていた不備を発見。法名限定のv2でも施行規則を漏らしたため、モデル出力を見る前にv3へ修正。対象9206条番号page/309親familyのsplit横断は0。v1/v2の失敗・コード・split/receiptは保持し、合格記録へ書き換えていない。JaQuAD全691記事の分割は不変。

最終v3はTRAIN候補16,966文書/20,262,193tokens、DEV2515文書/2,407,757tokens、保留521文書/681,308tokens。TRAINの82文書は重複除去後本文空で、次期scheduleから除外した。本文量は段落を個別encodeした値で、文書結合改行/BOS/EOSの学習target数と同一ではない。結合後TRAIN本文は20,520,663tokens、真のtargetsは20,537,547であり、差を新しい独立情報とは数えない。

話者/著者も別監査した。既存RPのTRAIN/DEV話者intersectionは0を維持したが、新しい会話原典は未収集。Wikiの最終編集者はTRAIN/DEVでBooks53人・Voyage20人が重複し、JaQuADは元著者/annotator IDがないため著者独立性は不明。最終編集者は全執筆者でも会話話者でもなく、文書分割だけで話者/著者分離を達成したとは報告しない。詳細はauthor-overlap-audit.json。

## Tokenizer/contextの適合性

現行語彙3997・独自BPEを変更せず使用。全対象をbyte完全復元できた。TRAIN全体は1.141文字/token（約0.876tokens/文字）で、RPの約1.70文字/tokenより非効率。全文書/段落のp50/p90/p99、未見glyph・UTF8 byte fallback、256/512/1024超過数はpipeline/artifactsのreceipt/subsetsに保存した。

| TRAIN source | 文字/token | 段落256超過 | 512超過 | 1024超過 |
|---|---:|---:|---:|---:|
| JaQuAD | 1.130 | 67.87% | 13.97% | 0.11% |
| Wikibooks | 1.142 | 7.81% | 2.59% | 0.78% |
| Wikivoyage | 1.169 | 5.05% | 0.92% | 0.21% |

全TRAIN段落では256超過11.07%だが、短い条文等が多い集計が説明文の長さを隠す。文書では11596/16966が256超過。集計だけからcontext256で十分とは判断しない。8k/16k語彙とcontext512/1024は**別比較の候補/資源設計**で、今回はfitや構造変更を実行していない。語彙を変えたtoken NLLを直接比較しない。

## 実際に読んだ品質とgenre

事前固定SHAで最終TRAINからfamilyごと最大1段落、JaQuAD20/Books30/Voyage30の80段落をroot assistantが全文読解した。superseded split分を含む読解unique数は82。正式な母語話者評価でも、population品質率の推定でも、人間執筆の証明でもない。原文と個別理由はquality-sample.json/quality-reading.json。

古事記の古語、漢文型、法令見出し、参考文献/食材リスト、架空の百科事典執筆例、削除された一覧を参照する文章、不自然な翻訳表現を確認した。本文を生成AIで補修せず、問題を保存した。現候補TRAINのtitle-based genre proxyは法令/解説約4.52M、日常生活系約0.93M、旅行地理約0.76Mで、未分類も約9.68Mある。proxyは人手分類や品質保証ではないが、全候補をそのまま日常会話の基盤へ入れる根拠もない。

## 内容必須DEV

32人手QA、12原文文章継続、24の明示したCodex作成INPUT/RUBRIC案を実装した。人手側は主に25fact QA＋7comparisonで、自然な人間の相談・条件付き応答の正解資料を揃えたとは言えない。24案には理由・説明・相談・条件・文脈最小対を含めるが、人間原文/人間評価/生成正解とは扱わず、学習データにも入れない。

与えられた情報から答える課題と外部知識を要するモードを分けた。全68件のencoding/context budget適合、最終TRAIN component重複0を確認。人間由来44件は33familyで、DEV内の同一記事/段落重複を独立標本として合算しない。長い完全文脈の4217QAはcontext192入力capで除外され、短文への偏りがある。

実査で「1870年の再版」を尋ねるのに「1873年の火災」を正解にした原注釈、質問と原文の作品名称が異なる原注釈を発見し、2件を無修正で隔離した。補充/AIによる正解修正はしていない。offsetが一致しても正解が意味的に正しい保証はない。

reserveのpayloadはパイプラインが扱っており、**封印TESTではない**。正式な独立会話TEST・母語話者2名の評価は未整備。今回新しいモデル生成をしていないのでDEV成績/日本語能力の改善は報告しない。runnerは重み未読のprepare68件のみ実行し、inferenceAuthorized=falseを維持した。

## 次の比較設計と実装

11.23M終端3470を共通初期model/Adam/RNGとして、controlは4RP窓、treatmentは2同一RP＋2新原文窓というデータ条件だけを変更する設計を作成した。BPE/構造/context/LR3e-5/CE/clip/固定終端選択は共通。本文・EOS・role頻度の違いはデータ条件の一部として計測し、「本文と全target量が同時に一致」とは言わない。

最初のfull256窓だけの案は、ほぼ全ての文書末尾EOSを落とすため拒否・保存。新案では両条件の各slotの有効長を一致させ、部分末尾窓を保持した。実データで2048step/arm、全target1,735,859/arm、native4096窓/2965文書、真の末尾777を監査。PAD361,293位置/armはlossから除外。bodyはcontrol1,514,256、treatment1,634,363で等しくない。元の2,097,152という予定数を実数へ流用しない。

ただしnative窓3424/4096がBooks、C++だけで839/4096。これは良い日常会話配分を選んだscheduleではなく、機構の実現可能性を確かめた**未認可の参照設計**。資料の人間原文性・genre・適切なsource比率を確定後、別の事前固定が必要。JaQuADのcontextsは選択された原文断片で、結合した派生文書が原記事の連続全文である保証はない。EOSは派生単位の終端として数えたもので、原記事本来の終端・段落間の意味接続を証明しない。

実モデルのforward/backwardは4バッチだけ実施。勾配/loss/clipは有限、100 Adam stateとstep3470を復元し、before/after全trajectory digestは同一。optimizer.stepはguardされ、呼出し試行0/更新0。勾配norm比1.469/1.826、cosine.313/.180は記述値で、改善の証拠ではない。新更新を経た完全再開/収束/言語評価は未検証。

継続は既存の語彙・構文・optimizer資産を保てるが、相槌への偏りと低LR/ほぼ常時clipの影響が残る。新規事前学習は分布と独自Tokenizerを設計し直せるが、初期資産を失い計算が必要。8k=8192ならd320で約12.568M、16k=16384なら約15.189Mに増え、既存embedding/Adam行と直接互換ではない。データ追加と同時の変更を容量だけの効果とはしない。詳細はresearch/RESOURCE_PLAN.md/NEXT_EXPERIMENT_PLAN.json。

## 資源・Go/No-Go

CPU quota2core/RAM8GiB/GPU0。ゼロ更新監査の最大RSSは約916MiB。既存実測1133targets/secを使うと新案約25.5分/arm、100M約24.5時間/armのCPU目安。GPU5000–20000tokens/secなら100M約1.4–5.6時間という値は仮定で、未測定。現11M/context256は8–16GiB GPUをprofile候補、27M級/長contextは12–24GiB等を検討するが確約値ではない。CUDA/AMP/大contextは未検証。

今回の作業ディスクは32GB。Gitに保存した旧成果のbyte一致済み作業コピーをsparse省略して約254MiB確保し、履歴・元重みは維持した。raw/source/corpus/scheduleは今度はGitへ永続保存する。今後100M以上のraw/派生/token/checkpoint世代/atomic saveには追加50–100GB程度を計画し、実際のデータ形式で見積り直す。

| 判断対象 | 結論 |
|---|---|
| 取得/正規化/出典/分割/Token分析の実装 | Go、実行・原典照合済み |
| ゼロ更新の数値整合性 | Go、実モデル4バッチ合格 |
| 10–30M候補量 | 約23.35M、ただし未採用混合authorship |
| 現候補をそのまま本学習へ投入 | **No-Go**：人間原文性、genre、引用、品質と意味familyの監査が未完 |
| 次の未認可scheduleをそのまま採用 | **No-Go**：Books/C++偏重、評価/人間応答資料/資源条件が不十分 |
| 正式な対話能力の採用判定 | **No-Go**：新しい能力評価未実行、独立会話TEST/母語話者評価未整備 |

次は現代的な日常説明・手順・理由説明・人間の内容応答を優先してadmission/genre配分を確定し、独立TESTと評価を整える。sourceの単純増量、追加epoch、loss係数変更、モデル拡大を自動で繰り返さない。R25正式anchor/R46比較基準/R48 No-Goと旧17/13/9/Pareto/反復条件、公開モデル/サイトは維持する。
