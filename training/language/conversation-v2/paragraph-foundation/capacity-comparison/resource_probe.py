"""Prepared real-update feasibility runner, currently blocked by durable capacity.
This is not a language-capacity comparison result. No pretrained assets are loaded.
"""
import pathlib,sys,argparse,json,shutil,time,random,resource
C=pathlib.Path(__file__).resolve().parent;P=C.parent;sys.path.insert(0,str(P))
from study_runtime import torch,read,sha,write,save,record,load_data,windows,pack,causal_ce,clip_grad_accurate,trajectory,digest,extra_rng,restore_extra_rng,restore_isolated
from core import initialize
CFG={k:read(P.parent/'diverse-foundation/resource-probes'/f'd{w}-c256.json')['config']for k,w in [('11M',320),('27M',512)]}
PARAMS={'11M':11225280,'27M':27397632}
DURABLE=pathlib.Path('/workspace/4k29')/P.relative_to(P.parents[3])/'private/capacity-feasibility'
RESERVE=256*1024**2

def requirement():
 # Both candidates must be feasible before starting either arm.
 largest=PARAMS['27M']*12+2*1024**2;required=2*largest+RESERVE;free=shutil.disk_usage('/workspace').free
 return dict(required_persistent_bytes=required,observed_free_bytes=free,pass_storage=free>=required,largest_full_state_estimate_bytes=largest,estimate_includes_FP32_model_Adam_and_2MiB_metadata=True,optimizer_updates=0,scope='Resource feasibility only, not language ability or measured27M training throughput')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--arm',choices=CFG);ap.add_argument('--check-only',action='store_true');ap.add_argument('--updates',type=int,default=4);a=ap.parse_args();r=requirement();write(C/'CURRENT_RESOURCE_GATE.json',r)
 if a.check_only:print(json.dumps(r));return
 assert r['pass_storage'],'No-Go: two-generation durable27M state capacity is insufficient; no model initialized or optimizer update'
 assert a.arm and a.updates==4,'This bounded first-stage runner is fixed at4 feasibility updates; larger scientific budget needs a new preregistration'
 protocol=read(C/'FEASIBILITY_PROTOCOL.json');assert sha(P/'corpus.jsonl.gz')==protocol['corpus_sha256']and sha(P/'schedule.json.gz')==protocol['schedule_sha256'];out=DURABLE/a.arm;out.mkdir(parents=True,exist_ok=True);assert not(out/'actual-updates.jsonl').exists(),'No silent rerun'
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);settings=dict(seed=61603,samplerSeed=61604,lr=3e-5,weightDecay=.05);model,opt,rng=initialize(CFG[a.arm],settings);assert sum(p.numel()for p in model.parameters())==PARAMS[a.arm]
 # initialize resets dropout RNG after width-dependent parameter initialization.
 random.seed(61605);__import__('numpy').random.seed(61605);corpus,schedule=load_data();trace=[];begun=time.monotonic();after2=None
 for i in range(4):
  needed=requirement()['largest_full_state_estimate_bytes']+RESERVE if(out/'checkpoint.pt').exists()else requirement()['required_persistent_bytes'];assert shutil.disk_usage('/workspace').free>=needed;x,y=pack(windows(corpus,schedule['arms']['B'][i]));opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);loss.backward();norm=float(clip_grad_accurate(model.parameters(),1));assert torch.isfinite(loss)and all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters());row=dict(step=i+1,targets=int(y.ne(-100).sum()),loss=float(loss.detach()),gradient_norm=norm)
  record(out/'actual-updates.jsonl',dict(event='intent',**row));opt.step();record(out/'actual-updates.jsonl',dict(event='completed',**row));opt.zero_grad(set_to_none=True);trace.append(row)
  obj=dict(trajectory=trajectory(model,opt,rng,[],i+1,[],i+1),extra_rng=extra_rng(),sampler=dict(source_schedule_sha256=protocol['schedule_sha256'],arm='B',cursor=i+1),trace=trace[:],purpose='capacity resource feasibility only',protocol_sha256=sha(C/'FEASIBILITY_PROTOCOL.json'))
  if i+1==2:after2=obj;save(out/'checkpoint.pt',obj)
  if i+1==4:save(out/'checkpoint.pt',obj)
 # Actual process-resume equality must be checked in the next stage, not claimed here.
 write(C/(a.arm+'-receipt.json'),dict(actual_updates=4,targets=sum(x['targets']for x in trace),seconds=time.monotonic()-begun,max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint_sha256=sha(out/'checkpoint.pt'),full_state_digest=digest(obj),updated_state_replay='Not yet executed; mandatory before any larger budget',language_capability_measured=False,formal_adoption=False))
if __name__=='__main__':main()
