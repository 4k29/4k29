"""SHA-bound actual terminal17 reading; NOT a grader for future generations."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();gp=E/'terminal-state-diagnostic/original17-python.json';assert sha(gp)=='2afdb6352711568fda49c28344f388a6fc8c84896e6661f5515d7b0758622e54';g=read(gp);notes=read(E/'reading-notes-terminal-original.json');assert notes['generationSha256']==sha(gp)and not notes['reviewPendingOtherRows'];assert len(notes['rows'])==17;keys=['grammar','meaning','connection','repetition','breaks','sentenceClosed'];refs={};bindings=[]
for n in [39,40]:
 P=R.parent/f'round{n}';bound={x['path']:x for x in read(P/'execution/artifact-manifest.json')['files']}
 for state,ap,bp in [('selected','new-validation.json','new-manual.json'),('terminal','terminal-state-diagnostic/original17-python.json','terminal-state-diagnostic/original17-manual.json')]:
  a,b=P/'execution'/ap,P/'execution'/bp
  for p in [a,b]:assert sha(p)==bound[str(p.relative_to(P))]['sha256']
  gg,mm=read(a),read(b);assert mm['generationSha256']==sha(a);bindings.append(dict(round=n,state=state,generationSha256=sha(a),manualSha256=sha(b)))
  for x,y in zip(gg['rows'],mm['rows'],strict=True):
   first=(x['prefix']+x['text'].split('。',1)[0]+'。')if '。'in x['text']else None
   if first:
    k=(x['prefix'],first);v={z:y[z]for z in keys}
    if k in refs:assert refs[k][0]==v
    refs[k]=(v,f'R{n}/{state}/{x["id"]}')
rows=[];reused=0
for i,(x,note)in enumerate(zip(g['rows'],notes['rows'],strict=True)):
 assert note['index']==i and note['id']==x['id']and note['fullPrefixAndContinuationActuallyRead'];h=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert h==note['prefixAndTextSha256'];r={k:note[k]for k in ['id','fullOutputMeaningful','fullOutputLoop','intrusiveRepetition','reason','prefixAndTextSha256']};k=(x['prefix'],(x['prefix']+x['text'].split('。',1)[0]+'。')if '。'in x['text']else None)
 if k in refs:v,loc=refs[k];r.update(v);r['firstSentenceScoreProvenance']='Same full prefix+observed first sentence as '+loc+'; unchanged components after actual new full reading';reused+=1
 elif 'freshFirstSentenceScores'in note:r.update(zip(keys,note['freshFirstSentenceScores']));r['firstSentenceScoreProvenance']='Fresh actual first-sentence reading of this exact continuation; no external factual certification'
 else:assert '。'not in x['text'];r.update(zip(keys,[0,0,0,0,0,False]));r['firstSentenceScoreProvenance']='No closed first sentence; actual repeated incomplete continuation'
 rows.append(r)
assert reused==12;result=read(R/'continue-10000/result.json');assert result['completedSteps']==10000 and result['bestStep']==9000
out=dict(generationSha256=sha(gp),meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),reviewer='Assistant actual complete selected17 reading; not independent blind human',actualRetainedUpdates=10000,selectedStep=9000,evaluatedStep=10000,all17FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=sum(x['fullOutputMeaningful']for x in rows),longLoopsPrimary=sum(x['fullOutputLoop']for x in rows),eos=sum(x['eos']for x in g['rows']),notNewTest=True,notUsedForSelection=True,firstSentenceSensitivityStrictDataInitiativeCategory=5,firstSentenceSensitivityPermittingColdEscapeAndPassiveHonorific=8,firstSentenceHistoricalBindings=bindings,rows=rows)
assert out['wholeMeaning']==0 and out['longLoopsPrimary']==15 and out['eos']==2;(E/'terminal-state-diagnostic/original17-manual.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('Recorded actual terminal17 reading; reused12 exact first-sentence components')
