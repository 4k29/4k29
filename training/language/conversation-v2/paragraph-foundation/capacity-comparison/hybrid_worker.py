"""Separate fresh-width actual-update feasibility only,4+2 calls per candidate.
Verified remote generations replace the need for two simultaneous local dense files.
"""
import pathlib,sys,argparse,subprocess,time,resource,random,fcntl
C=pathlib.Path(__file__).resolve().parent;P=C.parent;sys.path.insert(0,str(P))
from study_runtime import *
from core import initialize
CFG={k:read(P.parent/'diverse-foundation/resource-probes'/f'd{w}-c256.json')['config']for k,w in [('11M',320),('27M',512)]};PARAMS={'11M':11225280,'27M':27397632}
DEST=pathlib.Path('/workspace/4k29')/P.relative_to(ROOT)/'private/capacity-hybrid';RESERVE=256*1024**2

def capture(model,opt,rng,arm,cursor,trace,protocol_sha):
 return dict(trajectory=trajectory(model,opt,rng,[],cursor,[],cursor),extra_rng=extra_rng(),arm=arm,active_cursor=cursor,trace=trace[:],sampler=dict(source_schedule_sha256=read(C/'HYBRID_FEASIBILITY_PROTOCOL.json')['schedule_sha256'],source_arm='B',cursor=cursor),protocol_sha256=protocol_sha,purpose='Resource/numerical feasibility only; not a language-capacity result')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--arm',choices=CFG,required=True);ap.add_argument('--replay',action='store_true');a=ap.parse_args();protocol=read(C/'HYBRID_FEASIBILITY_PROTOCOL.json');assert read(C/'HYBRID_STORAGE_PREFLIGHT.json')['pass_all'];assert(P/'FINITE_COMPARISON_COMPLETE.json').exists();assert sha(P/'corpus.jsonl.gz')==protocol['corpus_sha256']and sha(P/'schedule.json.gz')==protocol['schedule_sha256'];psha=sha(C/'HYBRID_FEASIBILITY_PROTOCOL.json');
 for name,expected in protocol['source_code_sha256'].items():assert sha(C/name)==expected,name
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);out=DEST/a.arm;out.mkdir(exist_ok=True,parents=True);ledger=out/'actual-updates.jsonl';corpus,schedule=load_data()
 if a.replay:
  assert not(C/(a.arm+'-HYBRID_REPLAY.json')).exists(),'Do not repeat completed replay'
  prior=[json.loads(l)for l in ledger.read_text().splitlines()]if ledger.exists()else[];assert not any(e.get('phase')=='feasibility-replay'for e in prior),'Partial replay requires explicit audit, not guessing'
  manifest=C/'artifacts'/(a.arm+'-2')/'checkpoint.json';obj=legacy.loader.load_checkpoint(manifest,read(manifest)['sha256']);assert obj['protocol_sha256']==psha;model,opt,rng=restore_isolated(obj['trajectory']);restore_extra_rng(obj['extra_rng']);start=2;trace=obj['trace'][:]
 else:
  lock=(P/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not ledger.exists(),'Refuse implicit repeated probe calls';assert not(C/(a.arm+'-HYBRID_RECEIPT.json')).exists();random.seed(61605);__import__('numpy').random.seed(61605);model,opt,rng=initialize(CFG[a.arm],dict(seed=61603,samplerSeed=61604,lr=3e-5,weightDecay=.05));assert sum(p.numel()for p in model.parameters())==PARAMS[a.arm];trace=[];start=0
  write(C/('INITIAL_'+a.arm+'.json'),dict(config=CFG[a.arm],parameters=PARAMS[a.arm],model_digest=digest(model.state_dict()),training_torch_RNG_digest=digest(torch.get_rng_state()),private_python_RNG_digest=digest(rng.getstate()),fresh_Adam=True,optimizer_updates=0,protocol_sha256=psha))
  initial=capture(model,opt,rng,a.arm,0,trace,psha);size_estimate=PARAMS[a.arm]*4+2*1024**2;assert shutil.disk_usage(DEST).free>=size_estimate+RESERVE;save(out/'checkpoint.pt',initial);del initial
  subprocess.run([sys.executable,str(C/'hybrid_archive.py'),a.arm,'0'],check=True)
 compute=0.;begun=time.monotonic()
 for i in range(start,4):
  if pathlib.Path('/sys/fs/cgroup/memory.max').read_text().strip()!='max':assert int(pathlib.Path('/sys/fs/cgroup/memory.max').read_text())-int(pathlib.Path('/sys/fs/cgroup/memory.current').read_text())>1024**3,'Cgroup reserve'
  assert shutil.disk_usage(C).free>=3*(PARAMS[a.arm]*12+2*1024**2),'Scratch Git/archive reserve'
  # No dense local prior generation is removed unless already pushed/proven.
  estimate=PARAMS[a.arm]*12+2*1024**2;assert shutil.disk_usage(DEST).free>=estimate+RESERVE,'Hybrid single-state reserve';assert not(out/'checkpoint.pt').exists()
  tick=time.monotonic();x,y=pack(windows(corpus,schedule['arms']['B'][i]));model.train();opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);loss.backward();norm=float(clip_grad_accurate(model.parameters(),1.));assert torch.isfinite(loss)and math.isfinite(norm)and all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters());row=dict(step=i+1,targets=int(y.ne(-100).sum()),loss=float(loss.detach()),gradient_norm=norm,clipped=norm>1,lr=3e-5)
  phase='feasibility-replay'if a.replay else'feasibility-retained';record(ledger,dict(event='intent',phase=phase,**row));opt.step();record(ledger,dict(event='completed',phase=phase,**row));opt.zero_grad(set_to_none=True);compute+=time.monotonic()-tick;trace.append(row)
  if i+1 in [2,4]:
   obj=capture(model,opt,rng,a.arm,i+1,trace,psha)
   if a.replay:
    expected=read(C/'artifacts'/(a.arm+'-4')/'checkpoint.json')['full_state_digest'];assert digest(obj)==expected,'Full-state replay mismatch';write(C/(a.arm+'-HYBRID_REPLAY.json'),dict(exact_model_Adam_Torch_privatePython_globalPython_numpy_sampler_cursor_trace=True,additional_actual_optimizer_calls=2,full_state_digest=expected));print(a.arm,'exact2-to4 replay',flush=True);return
   save(out/'checkpoint.pt',obj);assert shutil.disk_usage(DEST).free>=RESERVE;del obj
   subprocess.run([sys.executable,str(C/'hybrid_archive.py'),a.arm,str(i+1)],check=True)
 if not a.replay:
  write(C/(a.arm+'-HYBRID_RECEIPT.json'),dict(retained_updates=4,retained_targets=sum(r['targets']for r in trace),retained_compute_seconds=compute,wall_seconds_including_archives=time.monotonic()-begun,max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,actual_retained_optimizer_calls=4,replay_pending=True,language_capability_measured=False,formal_adoption=False,protocol_sha256=psha))
if __name__=='__main__':main()
