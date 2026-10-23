"""Historical1000-step reading record only, SHA-bound; NOT a future grader."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];O=R/'execution/paired-daily-generation-1000';P=R.parent/'round39/execution/paired-daily-generation-1000';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
assert sha(O/'round39.json')=='1e4d00dd5dd6b085554891757b8b05fac999750d4eba41f6a24997deb8b67405'
assert sha(O/'round40.json')=='35c7ab16b2cb2d9a9aad340000d499770e0eab73ba027ff1f85f6a3feea10289'
a=read(O/'round39.json');b=read(O/'round40.json');history=read(P/'round39-reading.json');prior=read(P/'round39.json');assert history['generationSha256']==sha(P/'round39.json')
core=['id','prefix','text','tokens','eos','validTokens','validUtf8','inputTokens']
for x,y in zip(a['rows'],prior['rows'],strict=True):assert all(x[k]==y[k] for k in core)
old=dict(history,generationSha256=sha(O/'round39.json'),priorGenerationSha256=sha(P/'round39.json'),priorReadingSha256=sha(P/'round39-reading.json'),sameRawCoresAsHistorical=True,full12CurrentTextsAlsoActuallyRead=True)
newrows=[];changes={
2:(False,True,'友達と会う予定から日常生活の目的・基本的な活動をとる必要の不成立な説明へ逸れる。「確に示す」も不自然。有限73tokensのprimary非長期loop、日常生活の侵入反復はあり。'),
3:(True,True,'準備を継げず、降り降り・降雨を崩れた形で192tokens反復し、上限で切れる。'),
4:(True,True,'寝ると寝る・寝るを192tokens反復し、今夜の自然な行動につながらない。'),
9:(True,True,'週末の体験を答えず、日曜日についての不明な引用・入れ子の構文を繰り返す。87tokens有限EOSでもprimaryloop。有限の引用反復として非loopに寄せる感度では旧新同じ3件となる。')}
for i,(x,y,prior_read) in enumerate(zip(a['rows'],b['rows'],history['rows'],strict=True)):
 same=all(x[k]==y[k] for k in core)
 if same:r=dict(prior_read,exactOldCurrentRawCore=True)
 else:
  loop,intrusive,reason=changes[i];r=dict(id=y['id'],fullOutputMeaningful=False,fullOutputLoop=loop,intrusiveRepetition=intrusive,reason=reason,exactOldCurrentRawCore=False)
 r['prefixAndTextSha256']=hashlib.sha256((y['prefix']+'\0'+y['text']).encode()).hexdigest();newrows.append(r)
new=dict(generationSha256=sha(O/'round40.json'),actualEvaluatedUpdates=1000,all12FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=sum(r['fullOutputMeaningful'] for r in newrows),longLoopsPrimary=sum(r['fullOutputLoop'] for r in newrows),eos=sum(r['eos'] for r in b['rows']),notIndependentBlindHuman=True,notNewTest=True,notUsedForSelection=True,final10000AssessmentStillPending=True,rawFp32PythonOnly=True,rows=newrows)
assert new['wholeMeaning']==0 and new['longLoopsPrimary']==4 and new['eos']==10
for name,data in [('round39-reading.json',old),('round40-reading.json',new)]: (O/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
report=dict(actualUpdatesEach=1000,all24FullPrefixesAndContinuationsActuallyRead=True,identicalRawCorePairs=8,oldWholeMeaning=0,newWholeMeaning=0,oldLongLoopsPrimary=3,newLongLoopsPrimary=4,oldEos=10,newEos=10,meaningImprovementEstablished=False,interpretation='Tiny common/human NLL improvements do not establish free-generation gains; same whole0 and one more primary loop. TRAIN64 gap rises but correct NLL also worsens; distinguish relative contrast from correct-context prediction.',sensitivities={'finiteNewWeekendQuoteAsNonloop':'new loops3 instead of4; still whole0','broaderFiniteProseWeekendAndParkLoops':'both may gain loop counts; primary unchanged','unstatedOtherPersonDinnerQuestion':'weak alternative whole1 in BOTH identical texts, not primary'},notNewTest=True,notUsedForSelection=True,publicModelChanged=False,additionalOptimizerUpdates=0,fullTextSha256=sha(O/'FULL_GENERATIONS.md'),newReadingSha256=sha(O/'round40-reading.json'),oldReadingSha256=sha(O/'round39-reading.json'))
(O/'reading-complete.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
