"""Materialize only actually measured completed training and fully read generations."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';B=R.parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
a=read(E/'optimizer-audit.json');c=read(E/'comparison.json');p=read(R/'policy.json');s=read(R/'sources/manifest.json');new=c['models']['new'];old=c['models']['old'];assert a['actualCompletedUpdates']==10000 and a['optimizerCounters']==[20000]
met=a['bestWeightedDevelopmentNllPerByte']<p['nllSuccessThreshold'];lang=new['gatePassed'];write(E/'progress-goal.json',dict(actualCompletedUpdates=10000,nllSuccessThreshold=p['nllSuccessThreshold'],bestWeightedDevelopmentNllPerByte=a['bestWeightedDevelopmentNllPerByte'],nllCriterionMet=met,unchangedLanguageGatePassed=lang,progressCriterionMet=met or lang,developmentOnly=True,unseenGeneralizationEstablished=False))
manual=read(E/'new-manual.json');assert manual['generationSha256']==sha(E/'new-validation.json');reasons='\n'.join(f"- **{x['id']}**: {x['reason']}" for x in manual['rows']);tf=read(E/'recovered-train-loss.json');tfold=tf['models']['old']['metric']['nllPerUtf8Byte'];tfnew=tf['models']['new']['metric']['nllPerUtf8Byte']
text=f'''# Round19 結果 — 既存TRAINの参考資料境界修正

実際に**{a['actualCompletedUpdates']:,}追加optimizer更新**を完了。採用追加step **{a['selectedStep']}**、親optimizer10,000→最終20,000。最新model・AdamW・Torch/private Python RNGを同じcheckpointに保持し、採用FP32重みは別保存。要求回数を実績と代用しない。

共通DEV weighted segmentation NLL/UTF-8 byte: 初期 **{a['initialWeightedDevelopmentNllPerByte']:.12f}** → 最良 **{a['bestWeightedDevelopmentNllPerByte']:.12f}**。事前進捗閾値はRound17最良 **{p['nllSuccessThreshold']:.12f}**。NLL条件={met}、従来の厳格な言語ゲート={lang}。このNLLは40/30/30の分割診断で、独立した文章確率や言語能力の証明ではない。

全文意味 **{new['meaningfulFullOutputs']}/17**、初文 **{new['firstSentencePasses']}/17**、非ループ **{new['nonLoopOutputs']}/17**。同条件のRound16対照（Round18で固定rubricに合わせて再読解）はそれぞれ **{old['meaningfulFullOutputs']}/17・{old['firstSentencePasses']}/17・{old['nonLoopOutputs']}/17**。Round16元公式値4/17・2/17・0/17は改変しない。未知API名の未確認事実だけで失格にしないという元rubricを適用した再読解はRound18の記録を、全文一致の確認後に継承。閾値は変えていない。expanded17/parent13/original9と各物語/現代文groupで初文80%・非ループ90%・全文意味80%を要求。独立・盲検の人間評価ではない。

## 変更と再現

Round18実10,000はNLL0.974257670・全文意味0/17で事前進捗条件未達だった。MAFFの既存TRAIN原文93文書37,118文字のうち、参考資料見出しを本文末尾へ連結して短い完結本文を捨てる処理により、採用は6単位2,451文字（6.6%）だった。今回だけの主要介入は参考資料/参考文献/出典見出しより前で本文を閉じ、元のRound3 chain定義で未採用の**{s['admittedUnits']}単位・{s['admittedCharacters']:,}文字**を回復すること。

既存の全TRAIN単位・binary prefix・validation・独自語彙はそのまま保持。回復本文は元の原文の連続行とバイト単位で一致し、元文書のTRAIN割当を維持。元のdocument ID/startLineを使う40/30/30の分割seedと元のchain境界を使い、Round18の1文書1単位処理や新規取得原文は導入しない。全264viewの元バイト、mask一回被覆、ID一意性、sampling確率を独立に検査。

Round16と同じRound11最新model/AdamW/RNGからの兄弟対照。最新modelとbest modelを混ぜない。8層192次元・heads4・hidden768・context256・独自語彙5455・dropout.1・FP32・CPU2・batch8・seed系譜2049・一定LR2.2499999999999998e-5・500更新ごとの検証を保持した。データ変更で長さ分布とsamplerの軌跡・実target exposureは変わるため、同じ更新数だけで純粋な内容効果や統計的有意差とは言えない。

出典・著者・利用条件・原文SHAは既存の政府公開原文から保持し、加工表示を付す。`sources/license-records.json`に元の利用条件snapshotを保存。外部weights/tokenizer/生成API/生成教師・固定回答検索は使用しない。機械的重複監査で既存非TRAIN全627文書を読み、回復候補との64文字一致は0件。TEST本文を重複監査に読むことと、TESTのloss/生成/選択は区別し、後者は実施しない。元データに既知の短いcross-fold再利用や言い換え重複の可能性は残る。prepared dataの継承testRead:falseはstream構築scopeで、一切の原文アクセスなしという意味ではない。

初期model・AdamW・Torch/Python RNG・全DEVの完全一致、全勾配finite/nonzero、実counter、80,000row draw replayと終端private RNG・masked token/byte exposureを監査。実target tokens **{a['seenTargetTokens']:,}**、bytes **{a['seenTargetUtf8Bytes']:,}**、訓練elapsed **{a['elapsedTrainingSeconds']:.2f}秒**。`loss-history.csv`と`training-loss-events.csv`に実推移を保存。NumPy RNGは使用しない。

実行: `bash training/language/round19/execution/run.sh`。未完了だけ`--resume`、稼働中・完了済みは二重実行しない。通常は独立した`persistent.sh`が学習・機械評価・実counter/重みのdraft PR保存を行い、意味判定は読解後にのみ追加する。機械保存時のpending記録は当時のsnapshotで、最終判定は本報告とreview JSONを参照する。exportの2026-10-08は継承labelで実行日ではなく、SHA・counter・採用stepで識別する。

## 自己回帰生成と数値検証

旧新17件の同一書き出し、greedy全語彙、max192、true EOS、Python1threadを保持。`FULL_GENERATIONS.md`とJSONに全文・全token・prefix・EOS/UTF-8状態を省略なく保存し、修正や反復penaltyは行わない。これらは露出済みDEVで新TESTではなく、未見一般化を実証していない。

Python/JS全文一致: 旧 **{old['matchingSequences']}/17**・新 **{new['matchingSequences']}/17**。新reference logits最大絶対誤差 **{new['maxReferenceLogitError']:.12g}**。許容2e-4を維持。raw selected FP32対丸めexportは`export-rounding.json`、実分岐は`numerical-divergence.json`。Round10既知16/17 near-tie分岐を消さず、今回の一致を全入力への保証としない。

回復TRAINだけの採用後・教師強制NLLは旧 **{tfold:.12f}** → 新 **{tfnew:.12f}**（`recovered-train-loss.json`）。これはTRAIN診断で、自己回帰の全文成立や未見一般化とは別で、モデル選択には使わない。

## 各全文の読解

{reasons}

## 原因と次の改善

1. **容量**: 465万parameterを固定しており容量差は未試験。短い文の破綻やTRAIN/DEV差だけでは容量不足を確定できない。根拠なく大規模化しない。
2. **量・偏り**: 実在する単位化の欠落を回復したが、農業・FAQに限られMAFF row mass2.5%は固定。広い現代日本語の追加とは扱わない。回復量とsampling replayを踏まえ、次は利用条件の明確な多分野の人間原文を事前固定foldで増やす対照が候補。
3. **分割/境界**: 独自語彙と40/30/30を維持し264viewで原文バイトを確認。既存Round12のcuts除去も全文意味未達で、境界だけが原因との根拠はない。
4. **LR/optimizer**: 最新moments/RNGを完全復元しLRを固定。その別の効果は試していない。次のLR試験をデータ変更と同時には行わない。
5. **context**: 256を保持。短い出力の早い崩壊も評価し、長文脈だけを原因と断定しない。長文の能力は未実証。
6. **不足/過学習**: localな教師強制lossと自己回帰全文は別。固定旧TRAIN/DEV診断と回復TRAIN診断は対象が違う。loss全推移と実exposureを保存し、単に追加更新すれば解決とは判断しない。
7. **推論/実装**: Python/JS/raw丸め比較を実測。既存の因果性・明示attention一致・optimizer/RNG再開一致3テスト通過。実8層親で長さ64/128/256の未来suffixを変更しても先頭32logitの差0、後方は変化した。検査した範囲では未来参照による見かけのloss低下は見つからない。数値near-tieの限界は残す。
8. **評価/目的**: 既存17はDEVで、新TESTや独立読解ではない。未知名だけの失敗判定を避けて旧側も一貫して扱い、閾値を緩和しない。教師強制の局所改善と自由生成の差が残る場合、露出誤差・反復を抑える訓練目的の対照も候補だが、現時点で単一原因と確定しない。追加診断や別decodingで既存ゲートを代替しない。

公開モデル・Web回答挙動は変更しない。Checkpoint SHA `{a['checkpointSha256']}`、採用FP32 SHA `{a['selectedWeightsSha256']}`、JS SHA `{a['modelSha256']}`。全成果と入力のSHA/sizeは`artifact-manifest.json`に保存する。
'''
(R/'RESULTS.md').write_text(text);print(json.dumps({'actualUpdates':10000,'nllCriterionMet':met,'languageGatePassed':lang}))
