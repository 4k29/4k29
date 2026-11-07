# 独立Model Researcher：データ追加と資源の設計

これは新しい学習を実行した報告ではない。GOAL.md、epoch1 RESULTS/NEXT_STRATEGY、独立工学監査、自作Decoderを読んだ設計・算術監査で、optimizer更新は0回。正確な候補数値はRESOURCE_PLAN.json、再生成はbuild_resource_plan.py。

## 現状から推論できる範囲

中型11,225,280parametersは、RP本文2,456,893tokens・全target2,816,905の1epochを保持学習した。内容必須DEV0/24、自己継続0/4に対してNLLが下がった事実は、語彙/頻度への適合を意味しても内容応答の獲得ではない。容量不足は否定も断定もできず、8層のFFNを以前拡大して改善しなかった結果だけで容量の問題を排除しない。

中型2958/2958、小型2957/2958の継続更新でclip上限1が作用した。全重み/Adam momentsは有限で、二次moment非負、norm最大は約4.5–4.7なので「頻繁にclipした＝発散/実装不良」とは判断できない。一方、低いLR3e-5、batch4、clipping、短い学習量の最適化効率は未分離。新資料を足した後にLR/clipまで変更すると原因が混ざる。まず同条件で0更新の勾配・loss・状態監査を行い、別の最適化比較が必要かを判断する。

## 最初の比較：資料の置換だけを変える案

共通初期状態は中型3470のfull model/Adam/RNG、SHA `5ad249d2c8d5910090c9baba94f94483e9c037139d15b9c4360fd3e975409544`。8層/d320/heads4/FFN1280/context256/独自BPE3997、FP32、元のclip、同じLR3e-5を維持する。

現在の実装済み案は、controlを4個のRP window、treatmentを同じ2個のRP window＋新原文2個とするbatch4。新原文4096窓をSHA順で無置換選択し、各窓と**同じ有効target長1–256**のRP replacement窓を対応付ける。shared RP4096窓はreplacement4096窓と重複しない残りからSHA順で選ぶ。全2048更新でcontrol/treatmentの4スロットの有効長を一致させ、元のcore.packの4×256入力/target−100 PADを維持する。

現物から計算した全target予算は**各1,735,859**、ignored PAD361,293/arm。有効target数は204–1024/更新で、同一更新では両条件で完全一致する。control本文1,514,256/EOS110,323/role111,280、treatment本文1,634,363/EOS51,443/role50,053。本文targetまで完全一致とは言わず、差は資料条件の帰結として別記録する。sourceにないEOS/roleを作らず、objective maskや係数は変えない。

新原文は4096窓/2965文書/1139component、777個の真の文書末尾EOS（Books702/JaQuAD27/Voyage48）を保持する。全control8192窓、新原文4096窓はそれぞれ無置換でtarget位置の重複0。stride境界の1入力tokenの再利用を追加targetとは数えていない。sourceには重い偏りがあり、新原文窓はBooks3424/JaQuAD507/Voyage165、C++単一componentが839/4096。これは日常会話に適した承認済みmixtureではなく、学習投入はNo-Goのまま。sourceをadmit/変更する場合はscheduleを再作成・再固定する。

**全targetと本文targetを同時に正確一致させることは一般にはできない。** 比較の主要doseは全genuine-targetで、本文/EOS/roleとsource別doseを報告する。学習順序とsource/長さのmatchingによる選択bias、除外/重複、candidateとadmittedの違いを隠さない。実装/独立token再計算はbuild_matched_schedule.py、schedule_batches.py、audit_matched_schedule.pyとMATCHED_SCHEDULE_RECEIPT.jsonに記録した。新しいoptimizer更新は0。

新原文は文書BOS・元本文・真の文書末尾EOS、人間会話は従来のBOS/role/発話EOSを保持する。本文を架空の人間の発話に変換しない。これは新sourceに固有の表現契約を含むデータ条件で、意味内容だけを純粋に隔離する比較ではない。AIのuser/assistant役割を新たに獲得した比較とも呼ばない。文書をまたぐattentionや偽の窓末尾EOSは禁止する。

terminalを固定し、lossでselected checkpointを選ばない。preregisterしたDEV全文、内容必須DEV、旧17/13/9/Pareto/反復条件を維持し、NLL改善だけで成功にしない。封印TESTは今回開かず、全て見た資料を封印TESTと呼ばない。

## 却下したfull-window-only v0の証跡

257-ID/stride256の非重複窓で最後のpartial windowを除くと、原文長が1mod256の場合以外の文書EOSをほぼ全て落とす。RPの発話EOSは窓内に残るが、新説明文の終了を十分に学べない。したがって上記2,097,152targetのfull-window案を、そのまま学習へ進めない。

この欠陥は実学習前に発見し、NEXT_EXPERIMENT_PLAN_V0_FULL_ONLY_REJECTED.jsonへ保存した。現在の案は上記のmatched-length partial窓へ置き換え、各更新のactive-target数を両条件で一致させつつEOSを保持した。予算も現物1,735,859へ再計算しており、一律1024/更新・2,097,152とは記録しない。人工EOS挿入、黙ったmask変更、end-anchored窓の重複doseを隠すことは禁止する。少数full-windowの0更新勾配監査は計算の健全性だけを測り、このEOS問題の解決や新データ学習の収束を証明しない。

## 継続とfresh pretraining

| 選択 | 利点 | 弱点と必要な切分け |
|---|---|---|
| 今回終端から継続 | 自作model/Adam/RNGを活用し、日本語・EOSの既存学習を捨てない。データだけの比較を作りやすい | RPの相槌偏り、旧vocab/context、Adam履歴と低い継続LRを引き継ぐ。広い原文へ有利か不明 |
| 新しい自己学習BPEでfresh | TRAINだけから語彙/文字分割と広い原文分布を整えられる。旧IDの互換問題がない | 既存日本語学習を全てやり直す。Tokenizer/構成/初期化の同時変更はデータ追加との因果比較にならず、別系列・新予算が必要 |

8k/16kの語彙ではd320のパラメータ数も12.568M/15.189Mへ変わる。単なる同容量のTokenizer差と扱わない。現checkpointのtoken ID/embedding/Adam状態へ別の語彙をそのまま読み込めない。語彙拡張時の新行初期化とAdam年齢問題まで含めるため、最初の資料比較に混ぜない。Tokenizer比較は同じTRAIN原文・split・自己fit手順で別系列とし、同じraw bytes/文書の露出を主要比較にする。token数だけ一致させると原文の露出量が変わる。

context512/1024は現d320で11.307M/11.471M。位置embeddingだけを伸ばせば新しい位置は未学習で、optimizer状態もそのままでは一致しない。延長・新位置初期化・学習量を別条件で固定する。d512/context512は27.529Mだが、contextと幅を一度に変える容量比較にはしない。

## 資源の現実的な幅

FP32 model+gradient+Adamの静的部分は16N bytes、中型約171.3MiB。full checkpointは12N＋metadataで約129MiB。logits/FFN/attention/autograd/allocatorは別で、実際の中型CPU peak RSSは約951MiBだった。候補GPU8–16GiB等はprofile開始の目安で、必要最小値や確保済み資源ではない。GPUは0台、CUDA/AMPのtraining・再開・数値分岐も未検証。

以前の中型CPU実測約1133target/sを使うと、現在の案1,735,859targetsは算術上約25.5分/arm、二条件合計約51.1分。ただしPADも含む固定2048batchの計算費はtarget率だけで予測できず、実機のstep時間で再profileする必要がある。10M/30M/100Mは各約2.45/7.35/24.5時間/arm。新資料のpadding、context、I/O、同時処理で変わるため計測保証ではない。GPU5k–20ktarget/sという仮定なら100Mは約1.4–5.6時間/armで、現環境では測定していない。

10–30M独立tokensは最初の資料目標帯で、学習能力の必要十分量でも最適量でもない。100Mへの拡張はその十倍の許諾済み独立原文を要し、RPの反復で代用しない。uint32配列だけなら10M/30M/100Mは40/120/400MBだが、raw・正規化・近重複index・一時作成・checkpoint数世代・Git複製が増える。小規模corpus pilotで追加5–10GiB、100M以上の継続基盤で50–100GiBを運用計画帯とする。数学的必須容量ではないが、現環境の空き約23MiBでは耐障害な保存はできない。tmpfsはRAM8GiBの一部でhost消失に弱く、永続量として数えない。

## Go/No-Go

今は本学習No-Go。新資料の権利/品質・split/dedup・実量・framing・DEV/rubric・per-step schedule・予算・保存/再開を全てSHA固定していない。人間原文性の推定を確証に置き換えず、収集できた独立量と10–30M目標の不足を明示する。0更新のforward/backward監査だけは、TRAIN入力とコード/状態を事前固定しrootがGoとした後に行える。本格学習・有料GPU・公開置換・mergeは今回行わない。

## 実行した0更新監査と残る限界

rootがPREFLIGHT_PLAN SHA881c9b065f6e6c8d0a7affc1d4718da8b272b60d8b0a9c3ee9c0989ced44134eをcommit5f0cd2bで固定してGoとした後、source-balancedな2JaQuAD/1Books/1Voyageのfull TRAIN窓を使い4回のforward/backwardだけを実行した。optimizer.step呼出attempt0、実更新0。全100Adam stateは3470、moments有限・二次moment非負、初期model/Adam/Torch/private RNG/order/historyのtrajectory digestは前後ともd0dec20eed4131c242a374d9692bd6c11cb878c72c332280f836e741bc59b738で一致した。

controlのnorm1.699/1.827に対してdataadd2.496/3.336、比1.469/1.826、方向cosine0.313/0.180。全loss/勾配有限、postclip norm≤1、CPU process peak RSS938460KiB、約0.76–1.02秒/forward-backward batch。ratio/cosineは記述値で、事後にclipや係数を調整していない。preflight-result.jsonに全数値・body/EOS/role dose・RNG共有を保存した。

この0更新監査は元のfull-batch診断契約であり、partial schedule全2048batchの収束、終端学習、未知文章の生成、post-update再開一致を証明しない。partial/PADのsource読み込みは別の独立schedule auditで元core.packの最少有効長batch/真EOS包含batch等を検証した。学習開始はsource品質/権利/人間原文性、評価、予算、耐障害保存、learner実装・新更新後の再開が未解決なのでNo-Go。
