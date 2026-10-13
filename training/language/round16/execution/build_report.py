"""Report audited additional optimizer updates and the fixed progress criterion."""
import pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'execution';BASE=ROOT.parent
read=lambda p:json.loads(p.read_text())
a=read(OUT/'optimizer-audit.json');c=read(OUT/'comparison.json');r=read(ROOT/'continue-10000/result.json');p=read(ROOT/'policy.json');raw=read(OUT/'export-rounding.json');manual=read(OUT/'new-manual.json');replay=read(OUT/'sampler-replay.json');initial=read(OUT/'initial-equivalence.json')
assert a['actualCompletedUpdates']==r['completedSteps']==10000 and a['completedRun']
assert a['optimizerCounters']==[20000] and initial['optimizerCountersAtSnapshot']==[10000]
metric=next(h['validation'] for h in r['history'] if h['step']==r['bestStep']);start=r['history'][0]['validation']['nllPerUtf8Byte'];new=c['models']['new'];old=c['models']['old'];threshold=p['nllSuccessThreshold'];better=metric['nllPerUtf8Byte']<threshold;met=better or new['gatePassed']
goal=dict(retainedAdditionalOptimizerUpdates=10000,parentOptimizerUpdates=10000,latestOptimizerCounters=[20000],controlBestCommonDevelopmentNll=threshold,newBestCommonDevelopmentNll=metric['nllPerUtf8Byte'],nllImprovedOverControl=better,developmentLanguageGatePassed=new['gatePassed'],progressCriterionMet=met,nllImprovementDoesNotEstablishNaturalLanguage=True,naturalJapaneseEstablished=False,newTestGenerated=False,independentHumanEvaluation=False)
(OUT/'progress-goal.json').write_text(json.dumps(goal,indent=2)+'\n')
failure='\n'.join('- `'+x['id']+'`: '+x['reason'] for x in manual['rows'])
text=f'''# Round 16 — optimizer・RNGを保持した追加学習の結果

**実追加10,000更新を完了。共通開発NLL={metric['nllPerUtf8Byte']:.9f}、初文{new['firstSentencePasses']}/17、非ループ{new['nonLoopOutputs']}/17、全文意味{new['meaningfulFullOutputs']}/17。既存開発言語ゲート={new['gatePassed']}。** 今回の反復進捗基準（共通NLLがRound 11の最良値を下回る、または既存言語ゲートを合格する）={met}。NLLのみの改善は自然な日本語生成の改善を証明しない。公開モデル/Webサイトは変更していない。

## 事前固定した継続条件

Round 11ではstep7000の0.986095704から9500の0.978889879まで共通開発NLLが改善を続けた。一方、Round 13・14のジャンル再配分はNLL・全文意味の基準未達だった。この終盤の推移を根拠に、追加学習を一つの実験として選んだ。単なる無根拠な大規模化や更新数追加はしない。Round 15を含む直前判定はgoal-before-round16.jsonに保存した。

親はRound 11最新step10000の**対応したmodel・AdamW moment・Torch RNG・専用Python RNG**。beststate9500と最新optimizerを混ぜない。ジャンル比率は対照Round 11の45/10/10/15/10/2.5/5/2.5%、通常/Glyph/ランダム文字境界BPE40/30/30、独自語彙5455/merges512、8層dim192/heads4/hidden768/context256/dropout0.1/epsilon1e-5、466万パラメータ、原文/fold、batch8、seed系譜2049、FP32/CPU2/compileなし、AdamW/weight_decay0.05/clip1、開発検証500ごとを保持した。

元のcosine scheduleは10000更新で終了するため、追加区間では既存の厳密な終端LR **{p['learningRate']:.17g}** を保持する拡張規則を事前固定した。warmupやoptimizer・RNGを再開始していない。LR最適化との複合対照ではないが、元計画の範囲を超えるschedule拡張であることは明示する。データ数・新規原文の多様性やモデル容量は増やしていない。新しいseed・外部重み・学習済みTokenizer・生成API・別モデルの教師文・検索回答・テンプレート生成は不使用。

更新前にSHA・親checkpoint・全parameterの有限非ゼロ勾配・moment/RNGのロードとサンプル周辺確率を検証（追加optimizer更新0）。保存した追加step0は、親の最新weight・moment・LR・Torch/Python RNGと全開発ビュー/siteの測定に完全一致した。

## 実更新数・重み・再開

今回の追加実更新={a['actualCompletedUpdates']:,}/予定10,000。親optimizer counter10000→最新20000。最新重みの保持系譜={a['latestWeightLineageUpdates']:,}、採用追加step={a['selectedStep']}、採用重みの系譜={a['selectedWeightLineageUpdates']:,}。追加step0でoptimizer counterが0ではなく10000なのは正確な継続のため。採用beststateは推論用であり、再開は最新modelと対応するoptimizer/RNGから行う。

今回の実target token={a['seenTargetTokens']:,}、UTF8 byte={a['seenTargetUtf8Bytes']:,}、checkpoint訓練経過={a['elapsedTrainingSeconds']:.2f}秒。サンプラーを親から継続した追加step0のRNGから10,000回再生し、80,000行・末尾RNG・target token/byte数が一致。再生のoptimizer更新0。全weight/momentは有限FP32、NumPy RNG不使用。実計算回数を予定から推測していない。

checkpoint SHA `{a['checkpointSha256']}`

採用FP32 weights SHA `{a['selectedWeightsSha256']}`

model.js SHA `{a['modelSha256']}`

親最新checkpoint SHA `{p['parentCheckpointSha256']}`

modelVersionの日付文字列は既存exporter由来で、実行日や重みの同一性は表さない。識別にはSHAと採用stepを使う。

## 共通NLLと全文を分離する

| 測定 | 共通開発NLL/UTF8 byte |
|---|---:|
| Round 11採用9500（反復の固定基準） | {threshold:.9f} |
| Round 11最新10000＝今回追加step0 | {start:.9f} |
| 今回の採用追加step{a['selectedStep']} | {metric['nllPerUtf8Byte']:.9f} |

基準との差={(metric['nllPerUtf8Byte']/threshold-1)*100:+.3f}%。全21回のビュー/site別開発測定、sampled batchのtrain loss、実更新数をmetrics.json、train.log、loss-history.csv、training-loss-events.csvに保存した。単一seed・開発上の最良点選択で、独立TESTや統計的有意性を主張しない。

| 開発17件 | 旧Round 11採用9500 | Round 16 |
|---|---:|---:|
| 初文 | {old['firstSentencePasses']} | {new['firstSentencePasses']} |
| 非ループ | {old['nonLoopOutputs']} | {new['nonLoopOutputs']} |
| 全文意味 | {old['meaningfulFullOutputs']} | {new['meaningfulFullOutputs']} |

両モデルは同じ書き出し、全語彙greedy、max192、真EOS停止、Python1スレッド。全文・tokens・UTF8妥当性を無修正でJSONとFULL_GENERATIONS.mdへ保存した。旧判定は17件の再生成全文が元と完全一致した後だけ再利用。新モデルは全文を再読し、生成SHAに結合した理由を保存した。

初文80%以上・非ループ90%以上・全文意味80%以上をexpanded17/parent13/original9と物語/現代説明の全scope/groupへ適用する既存ゲートを維持。初文の合計9以上、grammar2、connection2、閉じた文、有効tokenの条件も変更していない。EOSだけで意味・非ループを合格にしない。旧比較モデルは採用9500、継続の初期重みは最新10000という差を明示する。NLLの継続効果は追加step0とも比較しており、生成変化を厳密に単独因果帰属するものではない。

## 全文の失敗と判定理由

{failure}

判定はassistant・非blindで、独立人間評価ではない。未知の固有名詞・省略された主語・APIの役割には不確実性があり、事実不一致や未知名だけを失敗の自動条件にはしない。既存17件は露出した開発診断で新TESTではない。過去policyのTEST参照が閲覧可能であった点も区別する。未見一般化は未実証。

## 推論の数値検査

Python/JS全文: 旧{old['matchingSequences']}/17、新{new['matchingSequences']}/17。新4参照logit最大誤差={new['maxReferenceLogitError']:.9g}、許容2e-4は不変。厳格exit値をparity-status.json、分岐をnumerical-divergence.jsonへ保存した。新しい一致でRound 10の既知の気象書き出しnear-tie分岐（旧16/17）を消していない。

生FP32採用checkpoint対7桁exportの全文一致={raw['matchingSequences']}/17。全生生成と誤差はexport-rounding.json。無修正の出力を対象とし、一般的な数値一致を保証しない。token粒度はgeneration-granularity.json、固定した同じTRAIN/dev標本のgapはtrain-development-gap.json。標本は全TRAINではなく、長さ・prefix条件・既存短文重複が残るためgapだけで過学習や容量原因を断定しない。

## 原因と次への推薦

lossと自己回帰の文法・意味・接続を分けて判断する。容量不足、原文の多様性・定型句、境界分割、LR、context256、不足/過学習、推論誤差、評価の限界という8仮説はRound 13/THREE_ROUND_RESULTS.mdと併せて参照。今回の継続は追加学習の効果を測る一対照で、他の原因を確定しない。NLLのみ改善なら語彙確率の改善という範囲に留める。

次の言語能力対照には、同じモデル・語彙・BPE比率・初期状態・LR・更新予算で、人間の現代日本語段落の質・文間接続・原文多様性を一因子として増やすことを推奨する。利用条件とTRAIN限定の原文調整、定型節重複の監査、独立人間評価と新たな未露出holdoutの固定を先に行う。今回、その原文追加実験は実行していない。公開モデル交換は実験モデルの明確な合格まで行わない。

## 再現可能な保存

policy.json/source-manifest.jsonは最初の追加更新前に固定し、途中変更していない。最新checkpoint、採用FP32/model.js、optimizer/RNG、実更新数、loss、全生成、比較と判定、数値診断を保存した。execution/artifact-manifest.jsonとverify_manifest.pyでSHAとサイズを確認できる。新規実行はexecution/run.sh。未完了checkpointからだけ同じcommandに--resumeを付け、完了済みは再開せずaudit/verifyで確認する。
'''
(ROOT/'RESULTS.md').write_text(text)
print(json.dumps(goal))
