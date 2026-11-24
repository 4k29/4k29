import pathlib,sys,json,math,random,statistics
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import train as t
from objective import causal_unlikelihood
t.torch.set_num_threads(1)
cp=t.torch.load(R.parent/'round11/continue-10000/checkpoint.pt',weights_only=False,map_location='cpu');m=t.Decoder(cp['config']);m.load_state_dict(cp['model']);m.train();t.torch.set_rng_state(cp['torchRng']);rng=random.Random();rng.setstate(cp['pythonRng']);info,values=t.load_partition(R/'multiview','train');strata,weights,masses=t.sampler(info['rows'],t.read(R/'policy.json')['genreSampling']);rows=[]
for b in range(16):
 width,data=t.draw(rng,8,strata,weights,masses);x,y=t.pack(data,values,width);z=m(x);ce=t.F.cross_entropy(z.flatten(0,1),y.flatten());ul,count=causal_unlikelihood(z,x,y)
 gc=t.torch.autograd.grad(ce,list(m.parameters()),retain_graph=True);gu=t.torch.autograd.grad(ul,list(m.parameters()))
 norm=lambda grads:math.sqrt(sum(float(g.double().square().sum()) for g in grads))
 cn,un=norm(gc),norm(gu);dot=sum(float((a.double()*b.double()).sum()) for a,b in zip(gc,gu,strict=True));rows.append(dict(batch=b+1,width=width,validTargets=int(y.ne(-100).sum()),negativeCandidates=count,ce=float(ce.detach()),ul=float(ul.detach()),ceGradientNorm=cn,ulGradientNorm=un,ulToCeGradientNorm=un/cn,cosine=dot/(cn*un) if un else None))
ratios=[r['ulToCeGradientNorm'] for r in rows if r['ulGradientNorm']>0]
out=dict(frozenParentCheckpointSha256=t.sha(R.parent/'round11/continue-10000/checkpoint.pt'),trainingIndexSha256=t.sha(R/'multiview/train.index.json'),batches=rows,medianUnscaledUlToCeGradientNorm=statistics.median(ratios),medianAtCoefficientPointOne=.1*statistics.median(ratios),additionalExperimentalOptimizerUpdates=0,optimizerInstantiated=False,trainOnly=True,noDevelopmentOrTestOrGenerationUsed=True,diagnosticScope='16 deterministic initial sampler batches at unchanged aligned Round11 weights, train mode dropout, separate process. No claim about late-training gradients or self-generated histories.')
(R/'execution/gradient-balance.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='batches'}))
