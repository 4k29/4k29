"""All17 full outputs read; reuse exact-control judgments only after equality audit."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
a=read(E/'old-validation.json');b=read(E/'new-validation.json');m=read(E/'old-manual.json')
assert sha(E/'new-validation.json')=='0e16b5705ac38165ee9857fd2767f1ece0f70e194a3c08d7517f80688a448139'
assert m['generationSha256']==sha(E/'old-validation.json')
assert a['maxNewTokens']==b['maxNewTokens']==192 and a['evaluationThreads']==b['evaluationThreads']==1
for x,y in zip(a['rows'],b['rows'],strict=True):
 assert all(x[k]==y[k] for k in ['id','prefix','text','tokens','eos','validTokens','validUtf8','inputTokens']),x['id']
m['controlGenerationSha256']=m['generationSha256'];m['generationSha256']=sha(E/'new-validation.json')
m['reviewer']='Assistant complete rereading of all17 raw prefix+continuations; exact control output equality verified; same fixed judgments. Not independent or blind human scoring.'
m['note']='All17 new complete texts/tokens identical to control Round22, including all failures. Exact judgment reuse after full rereading and equality audit; no grade changed because loss changed.'
(E/'new-manual.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
