"""Report only measured completed counters; unchanged gates and raw outputs."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
a=read(E/'optimizer-audit.json');c=read(E/'comparison.json');p=read(R/'policy.json');s=read(R/'sources/manifest.json');exp=read(E/'intervention-exposure.json');new=c['models']['new'];old=c['models']['old'];assert a['actualCompletedUpdates']==10000 and a['optimizerCounters']==[20000]
met=a['bestWeightedDevelopmentNllPerByte']<p['nllSuccessThreshold'];lang=new['gatePassed']
write(E/'progress-goal.json',dict(actualCompletedUpdates=10000,nllSuccessThreshold=p['nllSuccessThreshold'],bestWeightedDevelopmentNllPerByte=a['bestWeightedDevelopmentNllPerByte'],nllCriterionMet=met,unchangedLanguageGatePassed=lang,progressCriterionMet=met or lang,languageImprovementEstablished=False,developmentOnly=True,note='NLL criterion is progress only, not a language certification. Single seed, tiny source intervention, exposed development.'))
chain=read(E/'maff-chain-diagnostic.json');manual=read(E/'new-manual.json');reasons='\n'.join(f"- **{x['id']}**: {x['reason']}" for x in manual['rows'])
text=f'''# Round18 結果 — MAFF少数データ枠の原文多様化

実際に**{a['actualCompletedUpdates']:,} optimizer更新**を完了した。要求回数を実績として代用していない。採用追加step **{a['selectedStep']}**、親optimizer10,000→最終20,000。最新の重み・optimizer・Torch/Python RNGは同じcheckpointに保存し、採用FP32重みは別保存した。

共通開発weighted NLL/UTF-8 byte: 初期 **{a['initialWeightedDevelopmentNllPerByte']:.12f}** → 最良 **{a['bestWeightedDevelopmentNllPerByte']:.12f}**。事前の進捗閾値はRound17最良 **{p['nllSuccessThreshold']:.12f}**。NLL進捗条件={met}、厳格な言語ゲート={lang}。NLLだけで自然な日本語生成の改善を判定しない。

全文意味成立 **{new['meaningfulFullOutputs']}/17**、初文合格 **{new['firstSentencePasses']}/17**、非ループ **{new['nonLoopOutputs']}/17**。同条件のRound16対照はそれぞれ **{old['meaningfulFullOutputs']}/17・{old['firstSentencePasses']}/17・{old['nonLoopOutputs']}/17**。expanded17/parent13/original9、および物語・現代文の各scopeで、初文80%・非ループ90%・全文意味80%という従来の基準を維持。未知の固有名や事実性だけを意味失敗の理由にはしない。assistant全文読解であり、独立・盲検の人間評価ではない。

## 介入と対照

Round16と同じRound11最新step10,000のモデル・AdamW・Torch/Python RNGから追加10,000更新。Round17の最良重みと最新optimizerを混ぜていない。唯一の主要介入はMAFF TRAINへ人間執筆の説明原文 **10文書・5,867文字**を追加すること。旧MAFF6単位2,451文字を保持し、他ジャンルの全学習行も保持。独自語彙5,455、8層192次元、context256、40/30/30、固定ジャンル比、FP32・CPU2・batch8、seed系譜2049、一定LR2.2499999999999998e-5、500更新ごとの検証は不変。

MAFF確率2.5%は不変だが、追加原文の行確率は全体の約**{100*exp['newSourceMarginalRowProbability']:.3f}%**。これは農業分野の小規模介入であり、汎用的な現代日本語原文拡充や容量対照とは呼ばない。row長が変わるため実target exposureは一致せず、`sampler-replay.json`と旧対照のtoken/byte countsを参照する。単一seedのNLL差から因果効果や統計的有意差は確定できない。

## データ・再現性

出典は農林水産省の子ども向け農産物解説。公共データ利用規約第1.0版、出典URL・加工表示・取得時刻・HTML SHA・本文SHA・利用条件snapshotを`sources/`に保存。画像、キャラクター、第三者リンク、外部モデル生成を使用しない。HTML本文の段落を抽出しruby読みを省略する処理を明示。既存heldoutとの完全64文字一致を機械的に検査し、URLと本文SHAの重複も除外。新規3文書1,879文字はURL SHAによる事前予約で、学習・評価・tokenizerに未使用。旧foldを変更せず、新しいTESTの成績を主張しない。64文字未満の類似、意味重複、元データに既知の56短いcross-fold重複は残る限界である。

追加30viewの原文バイト一致・mask対象一回被覆・予約データ除外を独立に検査。全パラメータ勾配finite/nonzero、親重み・optimizer・RNGとstep0 snapshotの一致、固定source/code SHA、全80,000row draw replayと最終RNG・token/byte exposure・実counterを監査した。実target tokens **{a['seenTargetTokens']:,}**、bytes **{a['seenTargetUtf8Bytes']:,}**、訓練elapsed **{a['elapsedTrainingSeconds']:.2f}秒**。loss全推移は`execution/loss-history.csv`、100更新間隔のtraining eventは`training-loss-events.csv`。

実行は`bash training/language/round18/execution/run.sh`。未完了に限り同一環境・SHAの`--resume`で最新CPから復元し、完了済み・稼働中を二重実行しない。原文取得は外部サイト変更の影響を受けるため、完全再現には保存済みHTML・本文・prepared streamsを使う。`collect.py`/`prepare.py`は既存snapshotを上書きしない。

## 全文生成と数値一致

`execution/FULL_GENERATIONS.md`に旧・新の全17件を省略せず保存。JSONに全token、入力、EOS、UTF-8状態を保持。greedy・全語彙・max192・true EOS・Python1threadを両モデルで一致させ、反復ペナルティや生成後修正は使わない。

Python/JavaScript全文列: 旧 **{old['matchingSequences']}/17**、新 **{new['matchingSequences']}/17**。新reference logits最大絶対誤差 **{new['maxReferenceLogitError']:.12g}**。許容2e-4は不変。丸め前selected FP32との一致は`export-rounding.json`、near-tieの実traceは`numerical-divergence.json`に保存。Round10の既知の16/17分岐を取り消さず、今回の一致を全入力・全環境への保証とはしない。

## 各生成の失敗・成立判定

{reasons}

## 原因の切り分けと次の実験

1. **容量**: 同じ465万parameterを維持したため容量差は試していない。TRAIN/DEV差と短い初文後の崩壊だけでは容量不足を確定できず、大規模化を優先しない。
2. **データ量・偏り**: 既存MAFFの6単位を実際の原文追加で多様化したが、追加は全row約1.72%、農業だけで小さい。結果は汎用現代日本語コーパス増加の効果を決定しない。既存MAFF TRAIN原文93文書37,118文字のうち採用は6単位2,451文字で、短い本文に参考資料見出しを連結して末尾条件で落とすケースを確認した。参考資料直前で区切る診断では追加19,508文字が対象になり得る（`maff-chain-diagnostic.json`）。これは診断だけでRound18の訓練には追加していない。次はこの単位化の欠落を既存TRAINだけで回復する対照を優先し、その後に利用条件の明確な複数分野原文と事前固定heldoutを拡充する。
3. **分割・文字境界**: 独自語彙と40/30/30を固定、追加全viewが原文バイトと一致する。Round12のcuts除去でも全文意味0/17だった。全体の意味崩壊をencoding誤りだけで説明する証拠はない。
4. **LR・optimizer**: 親最新model/moments/RNGを一致させ、終端LRを固定。今回その効果は分離していない。LR変更を次のデータ変更と同時に行わない。
5. **context**: context256を固定。短い生成での局所反復・文法崩壊があるなら、長contextだけでは説明しにくい。長文は未検証。
6. **学習不足・過学習**: loss全推移と固定TRAIN/DEV診断を保存。NLL改善と自由生成は別。追加更新や過学習の断定は、target exposure・DEV反転・新原文量を踏まえて判断する。
7. **推論誤差**: Python/JSとraw/roundedの実測を保存。小さなlogit差・既知near-tie分岐は隠さない。同条件で両実装が同じ文章崩壊を出す場合、推論誤差だけでは説明できない。
8. **評価**: 17書き出しは既に露出したDEVで新TESTではない。主観判定や未知名の扱いの感度は残る。全raw文章と理由を保存し、今後は固定rubricの独立読解と新事前固定holdoutを追加する。ゲート緩和や短い初文だけへの切替は行わない。

新しい原文を増やす次の実験ではモデル・語彙・LR・view比を固定し、データ介入だけを比較する。機械的な完結性選別の微小NLL差や農業だけの小規模追加を、広い言語能力の成功と扱わない。外部学習済み重み・tokenizer・生成教師は引き続き使用しない。公開モデル・Web回答挙動は変更していない。

Checkpoint SHA: `{a['checkpointSha256']}`。採用FP32 SHA: `{a['selectedWeightsSha256']}`。JS SHA: `{a['modelSha256']}`。全成果と入力のSHA/sizeは`execution/artifact-manifest.json`に記録する。
'''
(R/'RESULTS.md').write_text(text)
print(json.dumps({'completedUpdates':10000,'nllCriterionMet':met,'languageGatePassed':lang}))
