"""Bind the four explicitly recorded completed readings; no new judgments."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();groups=[('original17','new-validation.json','new-manual.json',17),('daily12','daily-new-python.json','daily-new-reading.json',12),('native8','content-native-dev/new-python.json','content-native-dev/new-reading.json',8),('mrmp5','fixed-source-mrmp-dev/new-python.json','fixed-source-mrmp-dev/new-reading.json',5)];records=[];seen={}
for name,gp,mp,n in groups:
 g=read(E/gp);m=read(E/mp);assert sha(E/gp)==m['generationSha256'];assert len(g['rows'])==len(m['rows'])==n
 for x,y in zip(g['rows'],m['rows'],strict=True):
  h=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert x['id']==y['id']and h==y['prefixAndTextSha256'];key=(x['prefix'],x['text']);v=(y['fullOutputMeaningful'],y['fullOutputLoop']);assert key not in seen or seen[key]==v;seen[key]=v
 records.append(dict(group=name,rows=n,generationSha256=sha(E/gp),manualSha256=sha(E/mp),wholeMeaning=sum(x['fullOutputMeaningful']for x in m['rows']),longLoops=sum(x['fullOutputLoop']for x in m['rows']),eos=sum(x['eos']for x in g['rows'])))
out=dict(actualRetainedUpdates=10000,evaluatedSelectedStep=9500,all42FullPrefixesAndContinuationsActuallyRead=True,distinctPrefixFullTextPairs=len(seen),notIndependentBlindHuman=True,notNewTest=True,noOutputRepair=True,additionalOptimizerUpdates=0,groups=records);(E/'selected-full-reading-complete.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
