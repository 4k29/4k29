"""Report only completed measured training and SHA-bound complete reading."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
a=read(E/'optimizer-audit.json');c=read(E/'comparison.json');p=read(R/'policy.json');paired=read(E/'paired-exposure.json')
assert a['actualCompletedUpdates']==paired['actualUpdatesEach']==10000 and a['optimizerCounters']==[20000]
old=c['models']['old'];new=c['models']['new'];manual=read(E/'new-manual.json')
assert manual['generationSha256']==sha(E/'new-validation.json')
met=a['bestWeightedDevelopmentNllPerByte']<p['nllSuccessThreshold'];lang=new['gatePassed']
write(E/'progress-goal.json',dict(actualCompletedUpdates=10000,nllSuccessThreshold=p['nllSuccessThreshold'],bestWeightedDevelopmentNllPerByte=a['bestWeightedDevelopmentNllPerByte'],nllCriterionMet=met,unchangedLanguageGatePassed=lang,progressCriterionMet=met or lang,developmentOnly=True,unseenGeneralizationEstablished=False))
reasons='\n'.join(f"- **{x['id']}**: {x['reason']}" for x in manual['rows'])
tf=read(E/'recovered-train-loss.json');tfo=tf['models']['old']['metric']['nllPerUtf8Byte'];tfn=tf['models']['new']['metric']['nllPerUtf8Byte']
analysis=(E/'cause-analysis.md').read_text()
text=f'''# Round21 結果 — 反復抑制係数だけを変える対照

実**10,000追加optimizer更新**を完了。親optimizer10,000→最終20,000。採用は追加step **{a['selectedStep']}**、採用重み系譜 **{a['selectedWeightLineageUpdates']}**。最新model・AdamW・Torch/private Python RNGを同じcheckpointに保存し、採用FP32を別保存した。

通常CEの共通DEV weighted segmentation NLL/UTF-8 byteは初期 **{a['initialWeightedDevelopmentNllPerByte']:.12f}** → 最良 **{a['bestWeightedDevelopmentNllPerByte']:.12f}**。事前閾値は全ラウンド最良（Round19） **{p['nllSuccessThreshold']:.12f}**。NLL条件={met}、従来の厳格な言語ゲート={lang}。ULを検証NLLに混ぜていない。この40/30/30の分割診断は独立文章の確率や言語能力の証明ではない。

| 同一DEV17件 | 旧Round20 | 新Round21 |
| --- | ---: | ---: |
| 初文成立 | {old['firstSentencePasses']}/17 | {new['firstSentencePasses']}/17 |
| 非ループ | {old['nonLoopOutputs']}/17 | {new['nonLoopOutputs']}/17 |
| 全文意味成立 | {old['meaningfulFullOutputs']}/17 | {new['meaningfulFullOutputs']}/17 |
| 厳格な言語ゲート | {old['gatePassed']} | {new['gatePassed']} |

意味判定は全ての未修正prefix+continuationを読解しSHAで結合した。独立・盲検の人間評価ではない。旧判断はRound20と全文・token・設定が一致することを確認して継承し、旧記録を改変しない。初文80%・非ループ90%・全文意味80%をexpanded17/parent13/original9と各narrative/contemporary groupで要求する従来の閾値を維持。未知のAPI名・未確認事実だけを失格にせず、文法・関係・意味の持続を判断する。

## 単独の変更と対照

Round20の係数0.1では実10,000更新でNLL0.972678966・全文意味0/17・非ループ6/17だった。今回は **UL係数0.1→0.3だけ**を変更し、学習目的をCE + 0.3 × causal token ULとした。各位置までの直前64入力tokenの一意な非特殊token（ID>=6）を候補とし、正解の次tokenを除外する。候補の-log(1-p)を合計し、有効target数で平均する。p上限1-1e-6。maskされたtargetは除外。未来の入力や生成教師は使わず、元の正解文を変更しない。正しい反復・機能語を損なう副作用もあり得るため、通常CEとULを別記録した。

データはRound20の全prepared fileとSHAまで同一。回復TRAIN88単位19,508文字、既存TRAIN、validation、fold・独自語彙・ライセンスをそのまま使用し、新規収集・再分割・再学習Tokenizerは行っていない。出典・原文・利用条件は`../round19/sources/`とsource-manifestのSHAを参照。8層192次元・heads4・hidden768・context256・dropout.1・語彙5455・FP32 CPU2・batch8・40/30/30・ジャンル比・seed系譜2049・LR2.2499999999999998e-5・wd.05・clip1・500更新検証を固定した。

Round20と同じRound11最新のmodel/AdamW/RNGを使う兄弟対照で、Round20から更新数を延長した実験とは区別する。初期全DEV、weights/moments/RNGは完全一致。最終sampler Python RNG・Torch RNG・実target exposureもRound20と完全一致した（`paired-exposure.json`）。実target tokens **{a['seenTargetTokens']:,}**、bytes **{a['seenTargetUtf8Bytes']:,}**、elapsed **{a['elapsedTrainingSeconds']:.2f}秒**。同一seedの一対であり統計的な再現性・有意差は未確認。

`training-loss-events.csv`は100更新ごとの合成目的（CE+0.3UL）・CE・UL・候補数、`loss-history.csv`は固定DEV NLLの全推移を保存する。採用は通常CE NLLの最良checkpointで、生成の見た目で選び直さない。回復TRAINの採用後教師強制NLLは旧 **{tfo:.12f}** → 新 **{tfn:.12f}**。TRAIN診断であり、選択・未見一般化・自己回帰全文成立とは別。

## 数値一致と再現

greedy全語彙・max192・true EOS・Python1threadで同じ17書き出しを比較。全文は`FULL_GENERATIONS.md`とraw JSONに全token・全文字を保存し、修正・検索・テンプレート・反復penaltyを使わない。17件は露出済みDEVであり新TESTではない。TEST loss/生成/選択は未実施。既知の短いcross-fold原文重複や言い換えの可能性はRound20から継承し、データの完全な汚染なしを保証しない。

Python/JS全文一致は旧 **{old['matchingSequences']}/17**・新 **{new['matchingSequences']}/17**。新reference logits最大差 **{new['maxReferenceLogitError']:.12g}**。許容2e-4を維持。raw FP32対7桁丸めは`export-rounding.json`、実分岐は`numerical-divergence.json`を参照。Round10既知16/17 near-tie分岐を隠さず、今回の一致を全入力へ一般化しない。version内2026-10-08は継承labelで、SHA/counter/採用stepを識別に使う。

実行は`bash training/language/round21/execution/run.sh`。未完了のみ`--resume`、稼働中・完了済みを二重実行しない。checkpointは同一settings・RNG・AdamWを復元する。独立persistent.shが学習・機械比較・draft PR保存を行い、意味判定は全文読解後に追加。自動保存のpendingは当時のsnapshotで、最終結果は本報告とreview JSONを参照する。ULの独立参照計算・causal/gold/mask・極端確率・勾配・再開4テストと、実モデル勾配検証を通過。外部学習済みweights/tokenizer/API/他モデル教師を使っていない。

## 各生成全文の失敗・成立

{reasons}

## 原因分析と次の改善

{analysis}

公開モデル・Web挙動を変更しない。リポジトリ検証は`repository-validation.json`を参照し、公開側テストを実験言語能力と混同しない。Checkpoint SHA `{a['checkpointSha256']}`、採用FP32 SHA `{a['selectedWeightsSha256']}`、JS SHA `{a['modelSha256']}`。成果・入力のSHAとsizeは`artifact-manifest.json`に保存する。
'''
(R/'RESULTS.md').write_text(text)
print(json.dumps(dict(actualUpdates=10000,nllCriterionMet=met,languageGatePassed=lang)))
