# 日本語基盤学習・応答保持診断の結果

## 結論

採用条件は未達。公開モデル/サイト、正式採用R25、科学比較R46、旧17/13/9/Pareto/日常会話反復上限を変更していない。封印TEST、有料GPU/API、外部学習済み重み/Tokenizer、サブエージェントは使用していない。PRはDraftのまま、マージしない。

主たる問いは「自然な日本語」「未知入力への必要内容」「能力の保持」。全語彙greedyの無修正全文で判断し、NLL/EOSや出力の変化だけでは合格にしない。主24件は12文書componentから2prefixずつで、24独立文書ではない。採点はメインassistantの読解であり、独立した日本語母語話者評価ではない。

## データの実数と採用範囲

新規ネット取得0。PR94で収集済みの候補約20.26M TRAINを一括承認せず、JaQuAD公式TRAIN由来のWikipedia context、Wikibooks/Wikivoyage20261001公式dumpの限定部分を整備した。

- 3,939 TRAIN連続unit、元資料ID973、既知component/family685、元段落5,357。
- **独立原段落BPE 1,111,717tokens、原文1,284,517文字**。結合本文1,114,553tokensとの差2,836は人工的な段落結合LF等であり独立原文に加算しない。
- DEV140unit/42,260本文tokens。teacher-forced採点対象42,125。原典componentのTRAIN交差0、既知family/正規化完全重複0。
- source別の結合本文tokens: JaQuAD645,954、Wikibooks262,163、Wikivoyage206,436。料理/学校理科・文化・科学・地理に偏り、日常会話原文そのものではない。
- データSHA: `a0c8374e2918f589b0d967b515326ce108891de6bf62582c9e6a1821de37ea69`。schedule SHA: `c51b0ca3a08c954ddfea56dcb01ffca0a423a5525b808340a2645cb1672b7f48`。

`DATA_AUDIT.json`、最初のPLAN/receipt/FINAL_ADMISSIONの一部は「独立tokens」に結合本文数を使っていた。`ORIGINAL_TEXT_ACCOUNTING.json`で上記へ訂正した。凍結した入力や学習量を事後変更せず、元記録と訂正を両方保持する。

固定63標本と追加12標本を原文で読み、誤記/不正確な説明/図表依存/強い未検証断定等のunitとfamilyを隔離した。ライセンスはJaQuAD CC BY-SA3.0、Wiki CC BY-SA4.0、元URL/revision/history/加工SHAを各recordへ保持。旧rights/quality監査を再利用し、`FINAL_ADMISSION.json`はこの限定研究のみのリスク受容。全原文の人間執筆/全事実/第三者権利例外を完全認証したものではない。全候補の正式TRAIN採用、現在の旅行/法律助言や一般公開モデル利用を承認しない。

Wikiの既知最終editor横断を除外。JaQuAD原執筆者/全寄稿者/意味・地理familyの完全独立は未証明。人間評価用の新規提供者は0。OASST保留・JMultiWOZ隔離・MRMPC3者資料を無断で混入させていない。

## 入力・境界・計算条件

独自11,225,280パラメータ/8層/埋め込み320/heads4/FFN1280、独自BPE3997/context256/FP32/CPU2、dropout0.1、Adam/clip1。GPU0、8GiB環境。全条件を固定terminalで比較し、DEV best選択しない。

元の3470 checkpoint `5ad249d2c8d5910090c9baba94f94483e9c037139d15b9c4360fd3e975409544`から、model/Adam/RNGを**deepcopyして独立復元**した。PR99のAdam状態共有は再発していない。旧sampler状態は来歴として保持し、今回の進行は凍結scheduleとactive_cursorで管理する。

原文の途中や256窓境界にBOS/EOSを作らない。JaQuAD contextは独立抜粋なのでBOS/EOSなし。Wikiは元processed-pageの真の先頭/末尾のみ。PADは教師から除く。1token入力重複を持つ順次窓で、全教師位置は1回だけ。元本文はbyte roundtrip全件一致。未知nonASCII glyph4,353出現/853種類はbyte表現で保持され、文字欠落/既成Tokenizerへの置換はない。1,871unitが256超、362が512超、25が1024超。現原文は約1.155文字/tokenで256tokens≒296文字に限られる。

## 実際の学習

| 実行領域 | 実optimizer call | 保持更新 | 再開照合replay | 保持loss対象targets |
|---|---:|---:|---:|---:|
| run | 1578 | 1576 | 2 | 1111459 |
| mixed-run | 1578 | 1576 | 2 | 1111459 |
| lr-run | 1578 | 1576 | 2 | 1111459 |
| response-run | 516 | 512 | 4 | 13440 |

**合計実call 5,250、保持更新5,240、replay10。保持loss対象3,347,817targets。** 同じ原文を比較条件間で使っており、独立原文が3倍に増えた意味ではない。各基盤条件は同じ3470へ戻る独立実験であり、全条件のtargetsを一つのモデルへ累積したわけでもない。失敗した学習call、曖昧なintent、未完了予定更新を完了へ含めない。

1. 原文のみ: 1,576更新、1,111,459targets、元target位置を一回処理。LR3e-5。
2. 混合: 同じ3470初期状態から、各batchの2原文slotを元RealPersona TRAINへ置換。全slot入力長・教師位置・全target予算が同一。RealPersonaは既承認CC BY-SA4.0、元TRAIN3,152窓/2,722会話、教師位置反復0。元原文560,909独立位置＋既読RP481,059本文位置を提示。以前の282万targetsから既読の会話を新原文と数えない。
3. LRのみ: 混合のデータ・初期状態・Adam・RNGを固定し、LR3e-5→1e-4だけを明示的にoverride。元scheduleの連続継承という主張はせず、独立した一条件比較として実施。

基盤3条件の実時間は約27.1/21.7/18.8分、実効682/852/983targets/sec、最大RSS約1.05GiB。並行評価負荷が異なり速度の因果比較にはしない。全1,576更新でclipping、ノルム中央値2.51/2.34/2.21、全loss/gradは有限。詳細な分散/ノルム/損失はCSV/trace。clippingが常時という事実だけで失敗原因を断定しない。

## 全文生成の比較

| snapshot | 原文DEV NLL | 全文成立 | EOS | 有害反復 | 内容24DEV | 資料23DEV | 限定36DEV |
|---|---:|---:|---:|---:|---:|---:|---:|
| initial | 6.5722 | 2/24 | 24/24 | 0/24 | 0/24 | 0/23 | 0/36 |
| foundation | 4.9203 | 0/24 | 0/24 | 24/24 | 0/24 | 0/23 | 0/36 |
| foundation-mixed | 5.1369 | 0/24 | 0/24 | 24/24 | 0/24 | 0/23 | 0/36 |
| foundation-lr | 4.7713 | 0/24 | 0/24 | 24/24 | 0/24 | 0/23 | 0/36 |
| qa-only | 5.5290 | 1/24 | 15/24 | 9/24 | 0/24 | 0/23 | 0/36 |
| qa-rehearsal | 5.1745 | 0/24 | 1/24 | 23/24 | 0/24 | 0/23 | 0/36 |

原文の初期2/24は短いsuffixを整えて終了した最小限の成立で、説明段落の展開は0。主な失敗は擬似固有名詞、`1919年`等の日付反復、空白/改行ループ。途中の「例える」「発展しています」が整っても後続がループすれば全文成立にしない。未学習DEV NLLが6.57→4.77になっても、その後の自己生成は成立していない。

原文のみでは、正解人間会話履歴末端の平均EOS確率が0.6734→0.0157へ低下。混合では0.5716、LR変更では0.5279を維持するが、原文形式の自由生成EOSは回復しなかった。形式ごとの終端挙動に差がある。EOS頻度だけが単独原因だと証明したものではない。

学習原文に16文字以上の連続空白runは0。生成の空白無限反復を、そのまま同じ長い空白教材の暗記と説明する証拠はない。一方JaQuADは年号等が多く、genre/数字偏りは残る。`STYLE_DISTRIBUTION.json`の文字proxyは意味品質判定の代替ではない。

## 応答学習・保持診断の位置付け

基盤の事前移行条件（初期比で全文成立+2以上、反復増加なし）は不合格のまま。成功基準は緩めていない。ユーザー指定の探索/正式採用の区別に従い、**別の事後探索研究**として `RESPONSE_DIAGNOSTIC_PROTOCOL.md` を追記し、その診断の条件は自身の更新前に固定した。これは通常Phase6への合格や最初の事前登録通りの移行ではない。

初期は混合3e-5の固定terminal。LR系列の結果でbestを選ばない。両arm同じmodel/Adam/RNG/LR3e-5/clip1/Tokenizer/context/teacher位置/terminal選択。

- A: 1,024個の人手QA、256更新、6,720教師targets。134記事component、914原文context、953回答文字列。同じQA IDの反復0。
- B: 同じ各batchの2QA＋2つの日本語原文連続suffix。512QA＋512原文unit、256更新、同じ6,720教師targets。全slotの教師位置と提示長を一致。
- それぞれ提示167,711targets相当、lossを掛けるのは6,720のみ。提示tokenを教師tokenとして記録しない。

JaQuAD原質問/回答spanは人手注釈、入力外枠はprogram構成。完全な自然な人間assistant応答文ではない。文章内の範囲を質問と無関係に切り出し、元回答offset/根拠を検証。固定48標本を読解し、誤注釈/抜粋で失った根拠/曖昧さを隔離。候補TRAIN1,396、DEV103。全個別の母語話者/事実審査は未実施。

QAのrole3/4はUSER/ASSISTANTという新意味、旧人間A/Bと数値IDが同じでも別契約。EOSは構成した回答の終端。元人間の私生活をAI自身の正解にしていない。基盤→応答の形式/loss/data全体の差を単一要因効果と呼ばず、応答A/B間の配分のみを一条件比較する。

| snapshot | TRAIN16参照NLL | 必要文字列候補 | 未学習記事DEV32参照NLL | 必要文字列候補 |
|---|---:|---:|---:|---:|
| foundation-mixed | 5.4887 | 0/16 | 6.2050 | 0/32 |
| qa-only | 3.9567 | 0/16 | 4.8735 | 0/32 |
| qa-rehearsal | 4.1021 | 0/16 | 4.9268 | 0/32 |

必要文字列の出現は自動候補であり意味的合格数ではない。NLLは短い答えとEOSを含む。TRAIN16は暗記/適合の診断、DEV32は記事分離だが既に露出した診断で、話題/質問型は重なる。既存人手32DEVも別途同じ生成条件で評価。短いspanの適合や未知記事への一部成功を、一般会話/理由説明/相談の獲得へ拡大解釈しない。原文側の元全文成立が0なら、0を保っても能力保持成功とはしない。QA単独では全文成立1/24が短い既知suffixの回復に限られ、未知回答の成功にはつながらなかった。

応答教師は各条件6,720targets（Aはうち1,024がEOS）と小さく、256更新だけで学習可能性や容量の上限は断定できない。応答の勾配ノルム中央値はA9.18/B9.92、最大17.26/23.35で全更新clipping。基盤より強い縮小が掛かっており、次の最適化診断の根拠になるが、現在の結果だけでclippingが唯一の原因とも言えない。

応答診断の実時間はカーネル開始時刻と完成receipt時刻による概算約370秒。稼働中観測RSS約1.02GiBは標本であり全実行の最大値とは主張しない。詳細は `RESPONSE_RESOURCE_OBSERVATION.json`。

各checkpointの無修正出力、入力、全token列、raw bytes、停止理由を `evaluation/` と [GENERATIONS.md](GENERATIONS.md)へ保存。条件反転12、旧2件＋追加assistant作成2件の自己履歴3ターンも保存。新しい人間原文の評価とassistant作成の課題を混同しない。

## 不具合・再現性・保存

- 最初の旧評価はBOS前提で失敗。原型を保持し、独立decoderでBOS検査だけ除いた。学習や公開推論に変更なし。結果生成前の失敗/再実行を `EVALUATION_ATTEMPTS.json` に記録。
- 文字prefix24件中4件で元全文BPEとの分割差。主評価を上書きせず、最も近い妥当UTF8/source-token境界の別系列を保存。評価変更で元不合格を隠さない。
- 各実行の更新2→4を別プロセスで再開し、model/Adam/RNG/trace digest完全一致。replayも実callへ加算。`STATE_AUDIT.json`は全状態のAdam非共有、step、config、RNGを検証。
- atomic保存の故障注入で旧完成snapshot保持を確認。未完成.pendingを採用しない。基盤runnerは未保存更新をtrace照合replay、曖昧intentは停止。応答runnerは汎用resume CLIなしであり、事故時にledger/cursorの明示的照合が必要。
- checkpointは32MiB以下へlossless分割し、全byteSHAと全状態再読digestを確認。重複raw作業コピーだけを除いた。旧Git履歴/正式状態は保持。sparse省略した旧未採用R47/PR100/本研究のworking copyはGit blob一致証拠と復元方法を保存。

新しい研究checkpointの完全SHA:
- `foundation`: `36df9ab1d373faeaa7346ce54ead667cac80ab22094943defec155e02fa44a4f`
- `foundation-mixed`: `c56fadc15b1a501a5b3c427759a34317e97c23431740fd326f20bfb37a41fb3b`
- `foundation-lr`: `6759ef27a9a802c4a9b4c46b88885174630b0f433767faca85b9041ce9d942fc`
- `qa-only`: `22a5b91fe902e76170cc5e494a63899af44583d59195e7213f38784ea46301e9`
- `qa-rehearsal`: `90dc61eff44918c53cb8bcf9ad7aacb8175558b3f752c4453216d90c614809f0`

Python/JavaScriptは同じrawFP32重みの固定3prefix×最大4tokensで検証し、6状態合計66位置でargmax差0、独立短い生成差0、最大logit絶対誤差3.3379e-6（許容2e-4）だった。全語彙logits誤差、argmax、独立短い自己回帰の差を `parity-summary.json` と `parity-additional-summary.json` に保存。これは長文/全hardwareでの完全一致を証明せず、既知の旧near-tie数値分岐を撤回しない。正式モデルやサイトへ新重みを反映しない。

## テスト・成果物の確認

既存全体Nodeテストはローカルで962件中942合格、20件は旧R2–R10のsparse省略fixtureが存在しないためENOENTで失敗。全該当パスがGitに残りskip-worktreeであることを照合し、`LOCAL_FULL_SUITE.json`と全ログへ保存した。容量を使い切って旧fixtureを全展開する代わりに、完全checkoutのGitHub CIを別途確認する。`docs/app.js`構文検査は合格。

局所テスト19件合格（境界/教師位置・原文/既知family独立性・atomic故障・decoder互換性・同予算配分・実更新/replay台帳・raw bytes無修正を確認）。`verify.py` はstdlibで全source/artifact SHAと5 checkpointの全byte streamを確認する。GitHubの現在headのCI結果は [Draft PR101](https://github.com/4k29/4k29/pull/101/checks) を正本とし、古いheadの合格を新headの完了と記録しない。

## 次の判断

**正式採用/公開置換No-Go。** 成功の主張は全文・必要内容・未知入力・複数ターンの実測で行う。研究用の実行系と限定データ処理が動作しても、自然な対話能力の完成とはしない。

現在の証拠は、少量基盤学習の局所予測と自己生成の隔たり、会話/原文形式の終端分布の違いを支持する。約4Mtargets規模から容量不足を断定できず、作者/意味familyの完全独立も未確認。BPE/短いcontext、データ分布、最適化/反復、容量が同時に関与し得る。

次は `NEXT_STRATEGY.md` の原文配分一条件比較を優先する。追加10–30Mの権利確認済み生活/説明/理由/手順の独立原文と十分な実終端、20–50familyの新DEV、独立した母語話者評価を準備する。旧全文不合格を回避するため狭い教材を反復しない。更に広い100M以上への拡張は必要性/品質/資源を確認して別途判断する。

`RESOURCE_ESTIMATES.json`にCPU実測と仮定GPU見積を保存。現CPUで100Mtargetsは約28–41時間、1Bは約12–17日。GPUは未実測で、6NTによる11M/100Mtargetsは約6.74PFLOP、実効0.5–5TFLOPなら演算部分約0.37–3.74時間にI/O/評価等を加える。広告peak性能ではない。11MはGPU8–16GiB程度から実測、30–50Mは12–24GiBを候補にするが、今回利用しない。少なくとも10GiB、できれば20GiB以上の実験用空きを確保し、atomic二重保存・archive・Git増分も見込む。

今回の単一endpointが経験した教師量は、旧約282万＋今回の約111万＋応答6,720程度であり、汎用言語モデルとして少ない。100M/1Bへ増やせば達成できる保証はなく、独立原文と全文能力の改善を段階ごとに確認する。実用化までの所要時間は現在の結果から見積もれない。

モデル/Tokenizer/contextを拡大する場合は、それぞれ独立条件で比較する。現行466万/11Mの設計へ無条件に固執せず、データと計算量を含む能力上の根拠から選ぶ。
