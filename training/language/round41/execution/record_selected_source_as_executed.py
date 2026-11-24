"""SHA-bound actual selected source5 reading; NOT a future grader."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());gp=E/'fixed-source-mrmp-dev/new-python.json';assert sha(gp)=='aed718fbc9b48178e580b165399dac0e223c76f7625a001367c9b72c15974bf5';g=read(gp)
reasons=['仕事内容とポップコーンの香りの話への驚きは自然だが、おすすめの対象が示されずprimaryではつながりが弱い。12tokensEOS非loop。映画館の仕事/ポップコーンへの推薦と補う弱い代替whole1を残す。','子育てと赤ちゃん連れの母への話から、子供の子供の子供・お母さん・お出でになったを132tokens長く反復する。EOSでも所有・主述関係が崩れたprimaryloop。','購入場所/ロープウェイについての話にそうですねの後あとはと付け、何を追加で尋ねるかが曖昧。8tokensEOSのprimarywhole0非loop。ほかの購入場所を尋ねる省略と読めばwhole1の感度を残す。','スカイダイビングをしたいという発話に、あなたは何かのことですかと話者と対象・述語の関係が成立しない問いを返す。15tokensEOS非loop。過去の何かあったんですかという別文への代替解釈は移さない。','洗面所問題から今日は毎日を長く連打し、述語も意味も閉じず192tokensで切れる。primaryloop。']
rows=[]
for i,x in enumerate(g['rows']):
 assert x['validUtf8']and x['validTokens'];rows.append(dict(id=x['id'],fullOutputMeaningful=False,fullOutputLoop=i in [1,4],intrusiveRepetition=i in [1,4],contentBeyondBackchannel=False,explicitContextObjectReference=False,newInformation=False,reason=reasons[i],prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
core=['id','prefix','text','tokens','eos','validUtf8','validTokens','inputTokens'];bindings=[]
for n in [39,40]:
 P=R.parent/f'round{n}';bound={x['path']:x for x in read(P/'execution/artifact-manifest.json')['files']}
 for state,ap,bp in [('selected','fixed-source-mrmp-dev/new-python.json','fixed-source-mrmp-dev/new-reading.json'),('terminal','terminal-state-diagnostic/mrmp5-python.json','terminal-state-diagnostic/mrmp5-reading.json')]:
  a,b=P/'execution'/ap,P/'execution'/bp
  for p in [a,b]:assert sha(p)==bound[str(p.relative_to(P))]['sha256']
  gg,mm=read(a),read(b);assert mm['generationSha256']==sha(a)
  for x,y in zip(gg['rows'],mm['rows'],strict=True):
   for z,r in zip(g['rows'],rows,strict=True):
    if all(x[k]==z[k]for k in core):assert all(y[k]==r[k]for k in ['fullOutputMeaningful','fullOutputLoop']);bindings.append(dict(id=z['id'],round=n,state=state,priorGenerationSha256=sha(a),priorReadingSha256=sha(b)))
out=dict(generationSha256=sha(gp),reviewer='Assistant actual full source5 reading; not independent blind human',actualRetainedUpdates=10000,selectedStep=9000,evaluatedStep=9000,all5FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=0,minimalAcknowledgmentsOrOpinionActs=0,contentBeyondBackchannel=0,explicitContextObjectReferences=0,newInformationResponses=0,longLoopsPrimary=2,eos=sum(x['eos']for x in g['rows']),wholeMeaningSensitivityAllowingRecommendationAndLocationInquiry=2,notNewTest=True,notUsedForSelection=True,independentSpeakerCombinationFamilies=1,distinctPublicSpeakerIds=3,historicalExactCoreBindings=bindings,rows=rows);assert out['eos']==4;(E/'fixed-source-mrmp-dev/new-reading.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('Recorded actual source5 selected reading: whole0,loops2,EOS4; weak alternatives2')
