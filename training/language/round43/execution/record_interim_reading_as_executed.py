import pathlib,json,hashlib
R=pathlib.Path('/workspace/4k29/training/language/round43');P=R.parent/'round42';E=R/'execution';O=E/'paired-daily-generation-1000';H=E/'paired-human-dev-1000';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();bound={x['path']:x for x in read(P/'execution/artifact-manifest.json')['files']};oldg=P/'execution/paired-daily-generation-1000/round42.json';oldm=P/'execution/paired-daily-generation-1000/round42-reading.json';core=['id','prefix','text','tokens','eos','validTokens','validUtf8','inputTokens']

# Only the already-read fixed outputs below may be rebound.
assert sha(O/'round42.json')=='878b5e30b30ee36c98c9dd4ac19c664eec404d2d6bcbb0398cb152c93601b454'
assert sha(O/'round43.json')=='974de38c820c71158c349c00ec03cfae8a05f57c4dfeed582eb559ead17d1ccb'

for p in [oldg,oldm]:assert sha(p)==bound[str(p.relative_to(P))]['sha256']
m=read(oldm);assert m['generationSha256']==sha(oldg)
for n in [42,43]:
 p=O/f'round{n}.json';g=read(p);assert all(all(x[k]==y[k]for k in core)for x,y in zip(g['rows'],read(oldg)['rows'],strict=True))
 out=dict(m);out.update(generationSha256=sha(p),priorGenerationSha256=sha(oldg),priorReadingSha256=sha(oldm),all12FullPrefixesAndContinuationsActuallyRead=n==43,oldReadingReusedAfterExactCoreIdentity=n==42,reasonForHistoricalGradeReuse='Exact all12 full prefix/text/token/EOS/UTF8 cores match frozen R42 actual1000; new12 actually reread in current session, same primary judgments; no independent blind evaluation',scientificControl='round42',currentRound='round43')
 (O/f'round{n}-reading.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
new=read(O/'round43-reading.json');assert new['wholeMeaning']==0 and new['longLoopsPrimary']==4 and new['eos']==9
out=dict(actualUpdatesEach=1000,all12NewFullPrefixesAndContinuationsActuallyRead=True,old12ReadingVerifiedByExactCoreAndManifest=True,all24CurrentRawCoresEqualHistoricalRound42New=True,oldWholeMeaning=0,newWholeMeaning=0,oldLongLoopsPrimary=4,newLongLoopsPrimary=4,oldEos=9,newEos=9,meaningImprovementEstablished=False,expectedBeforeFirstChangedAuxUpdate1290=True,humanDevNllExactlyEqual=read(H/'complete.json')['oldHumanNllPerByte']==read(H/'complete.json')['newHumanNllPerByte'],notNewTest=True,notUsedForSelection=True,publicModelChanged=False,additionalOptimizerUpdates=0,fullTextSha256=sha(O/'FULL_GENERATIONS.md'),oldReadingSha256=sha(O/'round42-reading.json'),newReadingSha256=sha(O/'round43-reading.json'),sensitivity='same dinner-adequacy question alternativewhole1; finite prose/quote broaderloop5/6 as historical, no repair')
(O/'reading-complete.json').write_text(json.dumps(out,indent=2)+'\n')
pool=read(E/'context-auxiliary-pool.json')['rows'];ks={(x['document'],x['turn'])for x in pool};plan=read(E/'context-plan.json')['rows'];mask=[(x['document'],x['turn'])in ks for x in plan];assert sum(mask)==7;models={}
for label in ['old','new']:
 j=read(H/f'{label}-context.json');rows=j['rows'];assert len(rows)==64;groups={}
 for key,b in [('currentPoolPair',True),('notCurrentPoolPair',False)]:
  sub=[x for x,m in zip(rows,mask,strict=True)if m==b];groups[key]=dict(pairs=len(sub),meanCorrectNll=sum(x['correctNllPerToken']for x in sub)/len(sub),meanContextGain=sum(x['contextGain']for x in sub)/len(sub))
 models[label]=groups
assert models['old']==models['new']
(H/'context-membership-subsets.json').write_text(json.dumps(dict(actualUpdatesEach=1000,subgroupsPredeclaredBeforeTraining=True,currentPoolSize=1024,membershipRelativeToCurrentR43Pool=True,actualNewAuxPairsSeenBy1000=200,actualTrain64PairsUsedByNewAux=7,notHeldoutOrNewTest=True,models=models),indent=2)+'\n')
