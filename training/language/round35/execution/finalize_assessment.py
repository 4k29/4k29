"""Aggregate only completed actual updates and explicit already-read SHA-bound judgments."""
import pathlib,json,hashlib,datetime
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic';P=R.parent/'round34';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(R/'continue-10000/result.json');audit=read(E/'optimizer-audit.json');selected=read(E/'selected-optimizer-audit.json');numeric=read(E/'final-output-verification.json');new=read(E/'new-review.json');old=read(E/'old-review.json');terminal=read(D/'original17-review.json');oldend=read(P/'execution/terminal-state-diagnostic/original17-review.json')
assert r['completedRun']and r['completedSteps']==audit['actualCompletedUpdates']==10000 and audit['optimizerCounters']==[30000]
assert r['bestStep']==selected['selectedSnapshotActualUpdates']==8000 and selected['selectedOptimizerCounters']==[28000]
assert read(E/'selected-full-reading-complete.json')['all42FullPrefixesAndContinuationsActuallyRead']and read(D/'full-reading-complete.json')['all42FullPrefixesAndContinuationsActuallyRead']
assert numeric['newStateOutputsActuallyRead']==84 and numeric['savedStateOutputs']==168
assert all(numeric['parity'][s]['pythonJavascriptMatching']==numeric['parity'][s]['rawExportMatching']==42 for s in ['selected','terminal'])
for folder,group,filename,reading in [(E,'daily12','daily-new-python.json','daily-new-reading.json'),(E,'native8','content-native-dev/new-python.json','content-native-dev/new-reading.json'),(E,'mrmp5','fixed-source-mrmp-dev/new-python.json','fixed-source-mrmp-dev/new-reading.json'),(D,'daily12','daily12-python.json','daily12-reading.json'),(D,'native8','native8-python.json','native8-reading.json'),(D,'mrmp5','mrmp5-python.json','mrmp5-reading.json')]:
 m=read(folder/reading);g=read(folder/filename);assert m['generationSha256']==sha(folder/filename);assert len(m['rows'])==len(g['rows'])
 assert m['wholeMeaning']==sum(x['fullOutputMeaningful']for x in m['rows'])and m['longLoopsPrimary']==sum(x['fullOutputLoop']for x in m['rows'])
 for x,y in zip(m['rows'],g['rows'],strict=True):assert x['id']==y['id']and x['prefixAndTextSha256']==hashlib.sha256(json.dumps(dict(prefix=y['prefix'],text=y['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert read(E/'mechanical-full-assembly-complete.json')['savedFourStateOutputs']==168
assert read(E/'eos-exposure-audit.json')['eligibleAuxiliaryEosPositions']==161241
metrics=read(R/'continue-10000/metrics.json');oldmetrics=read(P/'continue-10000/metrics.json');anchor=read(R.parent/'round25/execution/new-review.json');anchornll=read(R.parent/'round25/continue-10000/metrics.json')['bestValidationNllPerByte'];current=metrics['bestValidationNllPerByte'];control=oldmetrics['bestValidationNllPerByte']
def pareto(ref,nll):return current<=nll and all(new[k]>=ref[k]for k in ['passed','fullOutputNonLoop','fullOutputMeaningful'])and (current<nll or any(new[k]>ref[k]for k in ['passed','fullOutputNonLoop','fullOutputMeaningful']))
daily=read(E/'daily-new-reading.json');olddaily=read(E/'daily-old-reading.json');enddaily=read(D/'daily12-reading.json');native=read(E/'content-native-dev/new-reading.json');endnative=read(D/'native8-reading.json');source=read(E/'fixed-source-mrmp-dev/new-reading.json');endsource=read(D/'mrmp5-reading.json');gap=read(E/'human-train-gap/complete.json')
practical_guard=(gap['models']['selected']['devNllPerByte']<=gap['models']['parent']['devNllPerByte']and daily['wholeMeaning']>=olddaily['wholeMeaning']and (12-daily['longLoopsPrimary'])>=(12-olddaily['longLoopsPrimary']))
nexttrial=dict(oneChangedLearningFactor='Human utterance-end EOS auxiliary coefficient1.0 to0.3 only',oldCoefficient=1.0,newCoefficient=0.3,scientificComparator='Round35',sameAlignedInitialization='Round28 latest full model/Adam20000/Torch/privatePythonRNG; lineage59000',requestedActualUpdates=10000,sameDataAndOriginalGoldTargets=True,sameModelTokenizerBpeSamplingLrSeedAndPrefixPolicy=True,sameOtherObjectivesAndInference=True,commonCeSelectorAndStrictGatesUnchanged=True,noCoefficientSweepInsideRound=True,notExecutedInRound35=True,reason='EOS preference increased at intended ends and also original non-newline content positions; selected common/human CE and original17 full meaning regressed, while only minimal context-compatible replies improved. Test a weaker coefficient without mixing data/decoding changes.')
adopt=dict(actualCompletedUpdates=10000,selectedStep=8000,terminalStep=10000,scientificControl='round34',initializationParent='round28',adoptionAnchor='round25',adopted=False,researchBaselineRemains='round25',publicModelChanged=False,strictLanguageGatePassed=False,naturalDailyConversationImprovementEstablished=False,minimalContextCompatibleSpeechActsObserved=True,notRobustSemanticCapabilityGain=True,commonDevelopmentNll=dict(initial=r['history'][0]['validation']['nllPerUtf8Byte'],old=control,new=current,newMinusOld=current-control,oldTerminal=oldmetrics['history'][-1]['validation']['nllPerUtf8Byte'],newTerminal=r['history'][-1]['validation']['nllPerUtf8Byte']),firstSentence=dict(old=old['passed'],new=new['passed'],oldTerminal=oldend['passed'],terminal=terminal['passed']),nonloop=dict(old=old['fullOutputNonLoop'],new=new['fullOutputNonLoop'],oldTerminal=oldend['fullOutputNonLoop'],terminal=terminal['fullOutputNonLoop']),fullMeaning=dict(old=old['fullOutputMeaningful'],new=new['fullOutputMeaningful'],oldTerminal=oldend['fullOutputMeaningful'],terminal=terminal['fullOutputMeaningful']),daily12=dict(oldMeaning=olddaily['wholeMeaning'],newMeaning=daily['wholeMeaning'],terminalMeaning=enddaily['wholeMeaning'],oldLongLoops=olddaily['longLoopsPrimary'],newLongLoops=daily['longLoopsPrimary'],terminalLongLoops=enddaily['longLoopsPrimary'],newEos=daily['eos'],terminalEos=enddaily['eos']),native8=dict(oldMeaning=0,newMeaning=native['wholeMeaning'],terminalMeaning=endnative['wholeMeaning'],newMeaningRequiringContent=native['wholeMeaningSensitivityRequiringContentBeyondBackchannels'],newMeaningConservative=native['wholeMeaningSensitivityRequiringExplicitReferentsAndContent'],newLongLoops=native['longLoopsPrimary'],terminalLongLoops=endnative['longLoopsPrimary']),fixedSource5=dict(oldMeaning=0,newMeaning=source['wholeMeaning'],terminalMeaning=endsource['wholeMeaning'],newMeaningConservative=0,terminalMeaningConservative=0,newLongLoops=source['longLoopsPrimary'],terminalLongLoops=endsource['longLoopsPrimary'],independentFamilies=1),additionalPracticalAdoptionGuardPassed=practical_guard,humanDevelopmentNllMustNotRiseGuardPassed=gap['models']['selected']['devNllPerByte']<=gap['models']['parent']['devNllPerByte'],dailyFullAndNonloopMustNotDecreaseGuardPassed=daily['wholeMeaning']>=olddaily['wholeMeaning']and daily['longLoopsPrimary']<=olddaily['longLoopsPrimary'],primaryParetoVersusScientificParent=pareto(old,control),primaryParetoVersusAdoptedAnchor=pareto(anchor,anchornll),reason='EOS停止と短い相槌・確認質問に限定した改善はあるが、共通/会話DEV NLLと従来17全文評価が悪化し、科学比較元・採用anchor双方に対するprimary Paretoを満たさない。自然な内容のある日常生成は未実証。strict gatesを維持して不採用。',notNewTest=True,nextExperiment=nexttrial)
assert not adopt['primaryParetoVersusScientificParent']and not adopt['primaryParetoVersusAdoptedAnchor'];write(E/'adoption-decision.json',adopt)
sensitivity=dict(selectedOriginal17=dict(primaryFirstSentence=new['passed'],primaryNonloop=3,primaryWholeMeaning=0,wholeMeaningRobustlyZero=True,nonloopCountingStrongSemanticRepetition=0,nonloopAllowingFiniteWarningExchange=4,firstSentenceLiteralBulletinAgentCanReduceCountBy1=True,firstSentenceEllipticalDataMeansCanIncreaseCountBy1=True),terminalOriginal17=dict(primaryFirstSentence=terminal['passed'],primaryNonloop=4,primaryWholeMeaning=0,wholeMeaningOpaqueProjectNameAlternative=1,wholeMeaningAlsoPermissiveWarningAgency=2,nonloopCountingStrongWeatherSelfReference=2,nonloopAllowingFiniteConferenceNarrative=5),sameStrictThresholds=True,noAlternativeChangesPrimaryJudgmentsOrSelector=True,notIndependentBlindReview=True)
write(E/'original-review-sensitivity.json',sensitivity)
final=read(E/'mechanical-status.json');final.update(actualCompletedUpdates=10000,fullOutputReviewPending=False,strictLanguageGatePassed=False,terminalStrictLanguageGatePassed=False,all42SelectedNewOutputsActuallyRead=True,all42TerminalNewOutputsActuallyRead=True,all168FourStateFullOutputsSaved=True,supplementalMechanicalEvaluationsCompleted=True,checkpointSelectorUnchanged=True,newOutputReadingEvidence=['selected-full-reading-complete.json','terminal-state-diagnostic/full-reading-complete.json'],oldReadingProvenance='Exact current selected core identity with prior completed Round34 readings; pinned historical terminal readings. Selected forecast and terminal JMA07 additionally reread for calibration; not a claim of fresh reading all old84.',adopted=False,fullOutputVerificationSha256=sha(E/'final-output-verification.json'),nextExperiment=nexttrial,finalAssessmentUtc=datetime.datetime.now(datetime.timezone.utc).isoformat());write(E/'final-assessment.json',final)
p=E/'mechanical-status.json';m=read(p);m.update(languageAssessment='Completed actual84 new full-output reading; strict gates failed; see final-assessment.json',strictLanguageGateAssessed=True,strictLanguageGatePassed=False,semanticReadingPending=False);write(p,m)
(R/'MECHANICAL_STATUS.md').write_text('# Final execution status\n\nActual10000 optimizer updates, Adam30000; selected8000 full aligned state, Adam28000. All84 new selected/terminal outputs read; strict language gates fail. Not adopted, no new TEST or public replacement. Earlier automatic pending records describe their creation time; final-assessment.json and RESULTS.md supersede them.\n')
header=f'''# Round35 結果 — 真の発話末尾へのEOS補助学習

実際のoptimizer更新**10000回**を1度完了。選択状態8000と最終状態10000の新しい84状態出力をすべて読んだ。うち2組は同じcore全文で、異なるcore出力は82件。同じ全文は同じ判定を維持した。**係数1.0は不採用**。停止・短い相槌には限定的な改善があるが、内容のある自然な日常会話を実証できず、共通/会話DEV NLLと従来17件の全文評価は悪化した。研究の採用anchorはRound25、公開モデル・サイトは変更していない。

[全168状態出力の無加工全文](execution/ALL_FOUR_STATE_GENERATIONS.md)、各manual/reading JSON、[数値照合](execution/final-output-verification.json)、[比較曲線](execution/paired-development.png)、[再現手順](REPRODUCTION.md)を保存。42固定入力×4状態であり168独立例ではない。旧モデルの全84件を今回新しく読み直したという主張でもない。

## 単一条件と実更新

Round34と同じaligned Round28 latestのmodel/Adam20000/Torch・privatePython RNG（weight lineage59000）から同じ10000更新を行う兄弟比較。唯一の学習変更は、human TRAINの真の発話末尾で元のunmasked targetがstandalone改行16の位置に、coefficient1.0のEOS2 CEを追加すること。和をbatchの**元のvalid target数**で割り、元の改行CEも残す。複合tokenに含まれる改行は対象外。R34の負例prefix境界条件は維持。

独自8層×192、heads4、FFN768、context256、語彙5455、4655808parameters、BPE40/30/30、human30%/旧genre70%、CPU2 FP32、batch8、seed系譜2049、LR2.2499999999999998e-5、wd.05、clip1、teacher4gramUL1、自己生成UL0.1/every10/greedy64/dropout train rescoring、推論greedy192と純CE checkpoint selectorは固定。追加model forwardや正例生成教師はない。

全10000の正例抽出、**15584824target tokens /54383388bytes**、最終Torch/Python RNGがR34と一致。EOS補助target161241か所、適用batch9163。対象数は独立したdraw replayと一致。自己生成負例1000回の初期prefixもすべてR34と一致し、全重み/momentsは有限。27 tests、147986全TRAIN行の独立mask検査、実モデル勾配、初期全DEV/model/Adam/RNG一致を学習前に確認し、388凍結入力のSHAも訓練中・訓練後に検証した。

latest full checkpoint SHA `{audit['checkpointSha256']}`、Adam30000・lineage69000。selected8000 full checkpoint SHA `{selected['selectedCheckpointSha256']}`、Adam28000・lineage67000。zero/actual200/1000/5000/selected8000/latest10000の6完全状態をlossless partsとSHAで保存。model.js/selected-weights.ptは推論用でありoptimizer再開用ではない。実学習時間{audit['elapsedTrainingSeconds']:.2f}秒。兄弟roundの更新を系譜へ足さない。

## 同一入力・同一生成条件の実測

| 指標 | R34 selected8000 | R35 selected8000 | R34 terminal10000 | R35 terminal10000 |
|---|---:|---:|---:|---:|
| 共通DEV CE NLL/byte | {control:.12f} | {current:.12f} | {oldmetrics['history'][-1]['validation']['nllPerUtf8Byte']:.12f} | {r['history'][-1]['validation']['nllPerUtf8Byte']:.12f} |
| 従来17 初文合格 | 10 | 10 | 8 | 7 |
| 従来17 非長期loop・主判定 | 5 | 3 | 6 | 4 |
| 従来17 全文意味・主判定 | 2 | 0 | 1 | 0 |
| 日常12 全文意味・主判定 | 0 | 0 | 0 | 0 |
| 日常12 長期loop・主判定 | 10 | 8 | 11 | 10 |
| 日常12 EOS | 0 | 4 | 1 | 2 |
| native8 全文意味・最小会話行為含む | 0 | 3 | 0 | 0 |
| native8 長期loop・主判定 | 8 | 2 | 8 | 5 |
| native8 EOS | 0 | 7 | 0 | 5 |
| 固定source5 全文意味・最小会話行為含む | 0 | 1 | 0 | 1 |
| 固定source5 長期loop | 5 | 2 | 5 | 2 |
| 固定source5 EOS | 0 | 4 | 0 | 3 |

共通DEV初期値0.971898957127。R35選択NLLはR34より**+{current-control:.12f}**で悪化。17/13/9の全scopeとnarrative/contemporary両群の厳格ゲートは、両新状態とも不合格。閾値は変更していない。新しいTEST結果はなく、反復して露出したDEVの1seed比較である。

native8のprimary3件は「そうなんですね！」「そうですね！」「そうですね。それはどんなものですか？」という短い相槌・確認質問。文脈に矛盾しない最小の会話行為として数えたが、固有内容の理解や会話発展を示さない。相槌を除く内容要求の感度では**1/8**、指示対象も厳格に要求すると**0/8**。source5の1件も「そうですね、おおー！」という驚きの相槌で、内容を要求すると**0/5**。同じ全文は両状態で同じ判定を維持した。source5は**1cast family・3公開ID**で、5独立集団ではない。これらを一般的な日常会話能力の成立とは認定しない。

日常12は短いEOSでも、まずはどこかにあるのかという不明な問い、AIが実験してみたいという格・接続の弱い返答、公園の問いと相槌の往復などで主判定0。挨拶を省略の多い希望表明として読む感度では1、雨の例を交渉対話として補う感度では2まであり得るが、primaryを変更せず保存した。日常loop8も有限な予報・食事・公園の扱いで7〜10、最終loop10は9〜11。反復の減少だけを意味改善にしない。

従来17ではR34の短く閉じていたENV05/MDN02が新selectedでは再び未閉鎖の法引用や「文字列を返します」の反復になる。terminalも旧STAT00の短い説明がPWA/サーバーの反復へ移り、全文意味0。未知名、創作、API事実の真偽だけでは失格にせず、主述・係り・内部意味・接続で判断した。末尾の軽微な生成上限切れは別に扱い、EOSによる不自然な早期終了を上限のせいにしない。解釈感度はoriginal-review-sensitivity.jsonと各readingに保存。

## EOSの作用と競合

TRAIN自己生成のhuman296回ではEOS終了**58→277**、即時EOS**1→4**、生成tokens15714→4588、反復負例位置9217→1448。固定DEVと異なる抽出prefixの訓練用64token診断であり、言語合格の証拠ではない。EOSによって自己生成負例の分布も変わるため、直接のEOS勾配と媒介効果をこの1条件から分離しない。

matched5000のTRAIN12行だけを使う事後診断では、補助対象67か所のEOS平均確率**0.032817→0.369663**、argmax0→37。元の正解NLLも0.892809→1.328342へ上がり、競合する改行/EOS教師の影響を示す。改行を含まない内容token1840か所でもEOS平均確率**0.001823→0.012167**、argmax3→45となった。これは過剰な終了傾向の懸念を示すが、45例すべてが不自然な代替終了だと証明はしない。詳細はEOS_LOCATION_DIAGNOSTIC.md。小さな相関したTRAIN subsetで一般化や意味を判定しない。

会話DEV99 NLLは**0.905768835509→0.910718571143**、R35terminal0.907144186733。固定TRAIN99は**0.869650598885→0.875082176939**、terminal0.870253833792。gapは0.03611824→0.03563639→0.03689035。EOS追加でtrain/dev両方の純CEが上がることは、単純な過学習の証拠ではなく競合目的の影響とも整合する。TRAIN99は全TRAIN平均でも全target既見の証明でもなく、DEVと長さ・話題が揃っていない。DEV99には完全重複1組がある。

## 原因の切り分け

- 容量: R27のFFN拡大で日常全文は改善せず、今回も容量を変えていない。一般的な幅・深さ不足は未否定だが、今回のEOS/NLL tradeoffを容量不足だけで説明しない。
- データ: R28/R29の人間会話30%/10%でも尤度改善と日常意味は別だった。今回も原文・抽出は同一で、停止だけを変えても内容生成の弱さが残る。新データを混ぜて作用を曖昧にしない。JMRDは人間原文候補の資料・licenseのみ確認し、対話データは未取得・未採用。READMEで露出した03042は将来採用時に除外する。既存CC-BY-SA原文の利用条件・分割を維持。
- 分割と境界: 全TRAINの正解・UTF8復元とmaskが正しい。補助対象はstandalone改行のみでview間比率が異なる。token化を変えず真の末尾を教える効果は測れたが、BPE一般の最適性を証明したわけではない。
- LR/optimizer: 初期model/moments/RNG、実counter、有限性とpaired抽出一致を確認。NLL波形はR34と類似し、8千回後の上昇も共有する。状態混在やoptimizer未更新の証拠はないが、LR最適性は未検証。
- context: 固定42入力は全て192tokenを生成できる余地があり、この評価の制限はcontext256より生成上限192が先。R34のcontext説明の補足を保存した。上限前の意味崩壊や短いEOS失敗はcontext延長だけで説明できない。
- 学習不足/過学習: さらに回数だけを増やすのでなく、EOS競合の強さを次に分離する。TRAIN/DEV99の両CE悪化とgapだけで過学習を断定しない。正例のraw target-byte coverageは同一親・抽出証明によりR33/R34と同じ58.1692%→82.6867%であり、意味や文脈のカバー率ではない。
- 推論誤差: 新selected42/42・terminal42/42でPy/JS全文、raw FP32/7桁export全文が一致。測定した意味失敗はこの数値差では説明されない。参考logit最大差1.1444091796875e-5、tol2e-4は不変。旧R10 near-tie16/17分岐は保持し、普遍的一致とはしない。旧export Py/JSは42件を現runtimeで再生成したが、旧raw FP32との比較は追加25件のみで元17は未再実行。旧terminalは凍結済み履歴資料。
- 評価: 露出DEV・1seed・assistant実読解で独立盲検ではない。短い相槌の成立と内容理解を区別し、すべての全文・理由・感度を残した。周期100更新のtraining lossは全てseqUL更新で、全更新平均ではない。旧saturationはR25比較、旧canonical gapはhumanを含む全TRAINではない。これらを科学比較R34や一般化評価と混同しない。

## 検証・採否・次

main pipeline exit0、追加source/terminal/TRAIN-gap評価も完了。新しい数値分岐やallowlist修復は不要だった。旧R34の修復履歴は旧資料として残す。Node962/962、既存公開回帰2580/2580を確認したが、実験言語ゲートの成功とはしない。全84新出力を実際に読み、旧selectedは全core同一の証明後に過去の読解を再利用した。

科学比較元R34、採用anchorR25の双方に対するprimary Paretoは不成立で不採用。追加practical guardの会話DEV99 NLL非悪化も不合格で、日常12の全文意味・非loop非減少のみは満たした。公開挙動は維持する。次は**EOS補助係数だけ1.0→0.3**を1ラウンドとして、同じaligned Round28開始状態・10000更新・data/正解/prefix/LR/seed/BPE/他目的/selector/推論を固定する。末尾での終了傾向を残し、内容位置のEOS上昇と純CE競合が弱まるかを測る。R35内で複数係数を試しておらず、次の実更新もR35の完了数へ足さない。内容が改善しなければ係数探索を盲目的に続けず、原文・会話構造の仮説へ進む。
'''
(R/'RESULTS.md').write_text(header)
(R/'README.md').write_text('''# Round35 — human utterance-end EOS auxiliary

実optimizer更新10000回を完了。selected8000/latest10000の新しい全文84件を実読解し、両状態とも従来の厳格言語ゲートは不合格。EOS終了と最小の相槌・確認質問には限定的な改善があるが、日常12全文意味0、共通/会話DEV NLLと従来17全文は悪化したため、係数1.0は不採用。公開モデル・サイトは変更していない。

変更は、human TRAINの真の発話末尾で元のunmasked正解がstandalone改行16の場合にEOS2補助CEをcoefficient1.0追加することだけ。元の正解とR34負例prefix条件を維持し、同じRound28 full model/Adam20000/RNGから10000更新する兄弟比較。[RESULTS.md](RESULTS.md)、[REPRODUCTION.md](REPRODUCTION.md)、[全168状態出力](execution/ALL_FOUR_STATE_GENERATIONS.md)、[比較曲線](execution/paired-development.png)、[最終判定](execution/final-assessment.json)を参照。

Py/JS・raw/exportは新84/84で全文一致。既知R10分岐はNUMERICAL_LIMITS.mdに残す。全checkpoint/moments/RNG/実数/SHAはpartsとmanifestで保存。次ラウンドはEOS係数だけ0.3へ下げ、データや推論を混ぜずに比較する。過去のmechanical pending記録は当時の状態で、この最終読解が後に追加された。新TEST・独立盲検の結果ではない。
''')
print(json.dumps(dict(actualUpdates=10000,selected=8000,originalSelected=[new['passed'],new['fullOutputNonLoop'],new['fullOutputMeaningful']],originalTerminal=[terminal['passed'],terminal['fullOutputNonLoop'],terminal['fullOutputMeaningful']],nativeMinimalMeaning=3,sourceMinimalMeaning=1,adopted=False,nextCoefficient=.3)))
