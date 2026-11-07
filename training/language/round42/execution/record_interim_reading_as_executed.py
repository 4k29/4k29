"""Historical SHA-bound actual1000 reading; NOT a future grader."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];E=R/'execution';O=E/'paired-daily-generation-1000';P=R.parent/'round41';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());assert sha(O/'round41.json')=='ca904aa31ac58642d4f90b3ae09a6bf0aa9a1d6f8bf76a115e3ab2d68c6962ff'and sha(O/'round42.json')=='94bc8f2aa6a4b063c930f2e463c1b011fa24a0384cf40bbe1eaeaf2880d034e5';a=read(O/'round41.json');b=read(O/'round42.json');hist=P/'execution/paired-daily-generation-1000';prior=read(hist/'round41.json');pm=read(hist/'round41-reading.json');bound={r['path']:r for r in read(P/'execution/artifact-manifest.json')['files']}
for p in [hist/'round41.json',hist/'round41-reading.json']:assert sha(p)==bound[str(p.relative_to(P))]['sha256']
assert pm['generationSha256']==sha(hist/'round41.json');core=['id','prefix','text','tokens','eos','validUtf8','validTokens','inputTokens']
for x,y in zip(a['rows'],prior['rows'],strict=True):assert all(x[k]==y[k]for k in core)
old=dict(pm,generationSha256=sha(O/'round41.json'),priorGenerationSha256=sha(hist/'round41.json'),priorReadingSha256=sha(hist/'round41-reading.json'),sameRawCoresAsHistorical=True,oldReadingProvenance='Previous actual R41 reading reused after frozen manifest and exact full core proof; not fresh blind evaluation')
changes={1:(False,False,'夕食は大丈夫ですか自体は自然な確認だが、このprefixで誰に何の十分さを尋ねるかが不明でprimary接続不十分。6tokensEOS非loop。残った材料で足りるかという普通の省略と読めばwhole1の代替を残し、文法破綻とはしない。'),2:(False,True,'友達と会う予定から日常生活の不成立な一般説明と地震防災へ逸れる。前半は日常生活にあるを重ねる侵入反復だが、後半は異なる防災の文へ進み、primaryでは長い同一内容の停滞loopと分ける。192cap/EOS無しだけでloopにしない。前半の有限反復をloopと数える代替は残す。'),3:(True,True,'準備を継げず、雨が降ると・降り降り・降を192tokens長く連打し、文と活用が崩れる。'),4:(True,True,'寝ると寝る・寝るを192tokens長く反復し、今夜の自然な行動につながらない。'),6:(False,False,'待ち合わせ時刻に天気の毒な人がいつもりですと返し、語結合・述語・話題が成立しない。未知の名前の外部真偽だけを理由にはせず、時刻相談との接続不足を記録する。14tokensEOS非loop。'),7:(True,True,'疲れへの応答がなく、今日はを何度も連打し、暮らす・泊まるへ逸れる。83tokensEOSでも長く停滞するprimaryloop。同じ全文のR40interim等と同じ判定。'),9:(False,True,'週末の体験を継げず、昼食や休みの質問という言葉についての不成立なメタ説明へ逸れる。78tokensEOSで二度の同じ引用は侵入反復だが、三文で異なる述語へ進みprimary非長期loop。有限引用反復を広くloopとする代替も残す。'),11:(True,True,'公園の公園という所有句の後、公園とか行きたいですねと同じ複合相槌を長く反復し、雨で予定を迷う相談を継げない。173tokensEOSでもprimaryloop。')}
rows=[];same=0
for i,(x,y,z)in enumerate(zip(a['rows'],b['rows'],pm['rows'],strict=True)):
 exact=all(x[k]==y[k]for k in core)
 if exact:r=dict(z,exactOldCurrentRawCore=True);same+=1
 else:
  loop,intrusive,reason=changes[i];r=dict(id=y['id'],fullOutputMeaningful=False,fullOutputLoop=loop,intrusiveRepetition=intrusive,reason=reason,exactOldCurrentRawCore=False)
 assert y['validUtf8']and y['validTokens'];r['prefixAndTextSha256']=hashlib.sha256(json.dumps(dict(prefix=y['prefix'],text=y['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();rows.append(r)
new=dict(generationSha256=sha(O/'round42.json'),actualEvaluatedUpdates=1000,all12FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=sum(x['fullOutputMeaningful']for x in rows),longLoopsPrimary=sum(x['fullOutputLoop']for x in rows),eos=sum(x['eos']for x in b['rows']),notIndependentBlindHuman=True,notNewTest=True,notUsedForSelection=True,final10000AssessmentStillPending=True,rawFp32PythonOnly=True,wholeMeaningSensitivityAllowingDinnerAdequacyConfirmation=1,loopSensitivityAlsoCountingFiniteProseWeekend=5,loopSensitivityAlsoCountingFiniteProseWeekendAndQuote=6,rows=rows)
assert same==4 and new['wholeMeaning']==0 and new['longLoopsPrimary']==4 and new['eos']==9
for n,x in [('round41-reading.json',old),('round42-reading.json',new)]:(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
report=dict(actualUpdatesEach=1000,all12NewFullPrefixesAndContinuationsActuallyRead=True,old12ReadingVerifiedByExactCoreAndManifest=True,all24OutputsCoveredByActualReadingOrVerifiedHistory=True,identicalRawCorePairs=same,oldWholeMeaning=0,newWholeMeaning=0,oldLongLoopsPrimary=2,newLongLoopsPrimary=4,oldEos=10,newEos=9,meaningImprovementEstablished=False,interpretation='Both common and human DEV NLL slightly worsen at1000; full daily meaning remains0. TRAIN64 aggregate correctNLL improvement is not unseen generalization:7 plan pairs are current auxiliary members and57others stillTRAIN. Do not tune conditions or selector mid-run.',sensitivities={'dinnerAdequacyQuestion':'weak natural omitted-material sufficiency confirmation alternative whole1; primary0, no output editing','finiteProseWeekendAsLoop':'new5 instead of4','finiteProseWeekendAndMetaQuoteAsLoop':'new6 instead of4'},notNewTest=True,notUsedForSelection=True,publicModelChanged=False,additionalOptimizerUpdates=0,fullTextSha256=sha(O/'FULL_GENERATIONS.md'),newReadingSha256=sha(O/'round42-reading.json'),oldReadingSha256=sha(O/'round41-reading.json'))
(O/'reading-complete.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
plan=read(E/'context-plan.json')['rows'];pool=read(E/'context-auxiliary-pool.json')['rows'];keys={(x['document'],x['turn'])for x in pool};indices={i for i,x in enumerate(plan)if(x['document'],x['turn'])in keys};assert len(indices)==7
used=set()
for line in(R/'continue-10000/context-preference.jsonl').read_text().splitlines():
 x=json.loads(line)
 if x['step']<=1000:used.update((pool[(x['firstPoolIndex']+j)%len(pool)]['document'],pool[(x['firstPoolIndex']+j)%len(pool)]['turn'])for j in range(x['pairs']))
subsets={}
for label in ['old','new']:
 data=read(E/f'paired-human-dev-1000/{label}-context.json');assert data['planSha256']==sha(E/'context-plan.json');d={}
 for flag,name in [(True,'currentPoolPair'),(False,'notCurrentPoolPair')]:
  rr=[x for x in data['rows']if(x['index']in indices)==flag];d[name]=dict(pairs=len(rr),meanCorrectNll=sum(x['correctNllPerToken']for x in rr)/len(rr),meanContextGain=sum(x['contextGain']for x in rr)/len(rr))
 subsets[label]=d
(E/'paired-human-dev-1000/context-membership-subsets.json').write_text(json.dumps(dict(actualUpdatesEach=1000,subgroupsPredeclaredBeforeTraining=True,membershipRelativeToCurrentR42Pool=True,actualNewAuxPairsSeenBy1000=len(used),actualTrain64PairsUsedByNewAux=sum((x['document'],x['turn'])in used for x in plan),notHeldoutOrNewTest=True,models=subsets),indent=2)+'\n')
