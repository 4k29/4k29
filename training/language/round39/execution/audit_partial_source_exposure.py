"""Read-only exact partial sampler replay; no model forward or optimizer update."""
import pathlib,sys,io,json,collections,torch,random,numpy as np,hashlib
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from batching import sampler,draw
torch.set_num_threads(1);raw=(R/'continue-10000/checkpoint.pt').read_bytes();cp=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=False);zero=torch.load(R/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False)
i=json.loads((R/'multiview/train.index.json').read_text());v=np.memmap(R/'multiview/train.tokens.bin',mode='r',dtype='<u4');tok=json.loads((R/'multiview/tokenizer.json').read_text());bl=np.array([len(bytes.fromhex(x))for x in tok['bytes']],dtype=np.int64);ss,w,m=sampler(i['rows'],cp['settings']['genreSampling']);rng=random.Random();rng.setstate(zero['pythonRng']);by=collections.Counter();views=collections.Counter();nt=nb=0
for _ in range(cp['step']):
 width,rows=draw(rng,8,ss,w,m)
 for r in rows:
  src='jmrd'if r['document'].startswith('jmrd:')else'realpersona'if r['site']=='human-chat'else'other';by[src]+=1;views[r['variant']]+=1;x=v[r['offset']+r['prefixLength']:r['offset']+r['length']];nt+=len(x);nb+=int(bl[x].sum())
assert rng.getstate()==cp['pythonRng'] and nt==cp['seen_tokens'] and nb==cp['seen_bytes'];assert {int(s['step'])for s in cp['optimizer']['state'].values()}=={20000+cp['step']}
a=dict(actualRetainedUpdates=cp['step'],checkpointSha256=hashlib.sha256(raw).hexdigest(),sourceRows=dict(by),viewRows=dict(views),sampledRows=sum(by.values()),exactOwnPythonRngAndTargetExposureReplay=True,seenTargetTokens=nt,seenTargetBytes=nb,additionalOptimizerUpdates=0)
out=R/'execution/partial-source-exposure';out.mkdir(exist_ok=True);(out/f"{cp['step']}.json").write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a))
