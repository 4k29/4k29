"""Draft TRAIN-only rollout diagnostics at fixed own parent; zero optimizer updates."""
import pathlib,sys,json,math,random
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import train as t
from sequence_objective import rollout_unlikelihood,repeated_generated_positions
t.torch.set_num_threads(1);parent_path=R.parent/'round11/continue-10000/checkpoint.pt';cp=t.torch.load(parent_path,map_location='cpu',weights_only=False);m=t.Decoder(cp['config']);m.load_state_dict(cp['model']);m.train();t.torch.set_rng_state(cp['torchRng']);rng=random.Random();rng.setstate(cp['pythonRng']);initial_rng=t.torch.get_rng_state().clone();info,values=t.load_partition(R/'multiview','train');strata,weights,masses=t.sampler(info['rows'],t.read(R/'policy.json')['genreSampling']);tok=t.read(R/'multiview/tokenizer.json');rows=[]
for batch in range(16):
 width,drawn=t.draw(rng,8,strata,weights,masses);x,y=t.pack(drawn,values,width);length=min(32,drawn[0]['length']-1);prefix=x[:1,:length];loss,record=rollout_unlikelihood(m,prefix,64,2,64)
 gradients=t.torch.autograd.grad(loss,list(m.parameters()));assert all(t.torch.isfinite(g).all() for g in gradients)
 norm=math.sqrt(sum(float(g.double().square().sum()) for g in gradients));full=record['tokens'][0].tolist();continuation=full[length:];raw=b''.join(bytes.fromhex(tok['bytes'][v]) for v in continuation)
 try:text=raw.decode('utf8');valid=True
 except UnicodeDecodeError:text=None;valid=False
 rows.append(dict(batch=batch+1,site=drawn[0]['site'],variant=drawn[0]['variant'],sourceUnit=drawn[0]['unit'],prefixTokens=prefix[0].tolist(),tokens=continuation,rawUtf8Hex=raw.hex(),validUtf8=valid,text=text,negativePositions=record['negativePositions'],generatedTokens=record['generatedTokens'],eos=bool(continuation and continuation[-1]==2),sequenceUl=float(loss.detach()),unscaledGradientNorm=norm))
assert t.torch.equal(initial_rng,t.torch.get_rng_state()) and all(t.torch.equal(v,cp['model'][k]) for k,v in m.state_dict().items())
out=dict(parentCheckpointSha256=t.sha(parent_path),trainIndexSha256=t.sha(R/'multiview/train.index.json'),tokenizerSha256=t.sha(R/'multiview/tokenizer.json'),maxNewTokens=64,historyWindow=64,prefixCap=32,greedyFullVocabulary=True,noOutputRepair=True,rows=rows,rolloutsWithRepeatedFourgram=sum(r['negativePositions']>0 for r in rows),negativePositions=sum(r['negativePositions'] for r in rows),generatedTokens=sum(r['generatedTokens'] for r in rows),globalTorchRngUnchanged=True,weightsUnchanged=True,optimizerInstantiated=False,experimentalOptimizerUpdates=0,trainingOnly=True,heldOutOrTestRead=False,usedForLanguageGate=False,limitation='Initial TRAIN-prefix diagnostic only. Generated tokens are prospective negative examples, never CE positives. No semantic score or unseen-generalization claim.')
p=pathlib.Path(__file__).resolve().with_name('initial-train-rollouts.json');p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
