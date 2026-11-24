"""Store root's actual24 full readings, bound to this exact R47 generation only."""
import pathlib,json,hashlib,copy
repo=pathlib.Path('/workspace/4k29');B=repo/'training/language';R=B/'round47';E=R/'execution';O=E/'paired-daily-generation-1000';P=B/'round46';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED_NEW_SHA='a8d641fef04598ad3a206e51f8ff3074046ab908ae47c7954564c8a0747b367e';assert sha(O/'round47.json')==EXPECTED_NEW_SHA
old=read(O/'round46.json');new=read(O/'round47.json');hg=P/'execution/paired-daily-generation-1000/round46.json';hm=P/'execution/paired-daily-generation-1000/round46-reading.json';prior=read(hm);bound={x['path']:x for x in read(P/'execution/artifact-manifest.json')['files']}
for p in [hg,hm]:assert sha(p)==bound[str(p.relative_to(P))]['sha256']
assert prior['generationSha256']==sha(hg)
for a,b in zip(old['rows'],read(hg)['rows'],strict=True):
 for k in ['id','prefix','text','tokens','eos','validTokens','validUtf8','inputTokens']:assert a[k]==b[k]
oldreading=copy.deepcopy(prior);oldreading['generationSha256']=sha(O/'round46.json');oldreading['historicalJudgmentsExactlyPreserved']=True;oldreading['currentFullReadingAlsoPerformed']=True;(O/'round46-reading.json').write_text(json.dumps(oldreading,ensure_ascii=False,indent=2)+'\n')
rows=[];identical=0
for i,(a,b,y)in enumerate(zip(old['rows'],new['rows'],prior['rows'],strict=True)):
 assert a['id']==b['id']==y['id']and a['prefix']==b['prefix'];z=copy.deepcopy(y)
 if i not in [4,10]:
  assert a['text']==b['text'];identical+=1;z['judgmentProvenance']='Exact full prefix+continuation equals verified R46 actual1000, and actually reread by root in current24-output comparison'
 else:
  assert a['text']!=b['text'];z.update(fullOutputMeaningful=False,fullOutputLoop=True,intrusiveRepetition=True,judgmentProvenance='Fresh changed full output actually read in R47')
  z['reason']=('寝るのが寝るので寝るから寝ると寝るを長く循環する。終盤の反復の配置は変わったが、今夜の行動の主述と意味は成立せず192token未完loop。'if i==4 else'近況の質問から武蔵野の名詞連鎖と見るを長く循環する。冒頭が作るから見てみたいへ変わっても、名詞修飾が崩れ反復が支配的で未完。未知の地名や事実の真偽だけで落とさない。')
 z['prefixAndTextSha256']=hashlib.sha256(json.dumps(dict(prefix=b['prefix'],text=b['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();rows.append(z)
assert identical==10
out=dict(generationSha256=EXPECTED_NEW_SHA,noteSourceSha256=sha(pathlib.Path(__file__)),actualRetainedUpdates=1000,evaluatedStep=1000,all12FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=sum(x['fullOutputMeaningful']for x in rows),longLoopsPrimary=sum(x['fullOutputLoop']for x in rows),eos=sum(x['eos']for x in new['rows']),notIndependentBlindHuman=True,notNewTest=True,notUsedForSelection=True,noOutputRepair=True,sensitivities=prior['sensitivities'],rows=rows)
assert (out['wholeMeaning'],out['longLoopsPrimary'],out['eos'])==(0,3,9)
(O/'round47-reading.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');h=read(E/'paired-human-dev-1000/complete.json');summary=dict(actualUpdatesEach=1000,all24FullPrefixesAndContinuationsActuallyRead=True,identicalFullPrefixAndContinuationPairs=10,changedFullOutputs=2,oldWholeMeaning=prior['wholeMeaning'],newWholeMeaning=out['wholeMeaning'],oldLongLoopsPrimary=prior['longLoopsPrimary'],newLongLoopsPrimary=out['longLoopsPrimary'],oldEos=prior['eos'],newEos=out['eos'],humanDevNllControl=h['oldHumanNllPerByte'],humanDevNllNew=h['newHumanNllPerByte'],broadMeaningOrGeneralizationImprovementEstablished=False,trainingConditionUnchangedAfterInterim=True,notNewTest=True,notUsedForSelection=True,rawFp32OnlyNoInterimJavascriptClaim=True,fullTextSha256=sha(O/'FULL_GENERATIONS.md'),oldReadingSha256=sha(O/'round46-reading.json'),newReadingSha256=sha(O/'round47-reading.json'),additionalOptimizerUpdates=0)
(O/'reading-complete.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
