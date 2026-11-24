"""Full inherited-state restoration and disjoint storage audit; no updates."""
import pathlib,sys,json,copy,resource,time
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P.parent/'modern-corpus'))
from next_runtime import torch,restore_isolated,trajectory,digest,restore_extra_rng,extra_rng
started=time.monotonic();torch.set_num_threads(2)
obj=torch.load(P/'private/source-B-6361.pt',map_location='cpu',weights_only=False);s=obj['trajectory'];before=digest(s)
a,oa,ra=restore_isolated(s);b,ob,rb=restore_isolated(s)
assert digest(s)==before
for pa,pb in zip(a.parameters(),b.parameters()):assert pa.data_ptr()!=pb.data_ptr()and torch.equal(pa,pb)
for sa,sb in zip(oa.state.values(),ob.state.values()):
 for k in sa:
  if torch.is_tensor(sa[k]):assert sa[k].data_ptr()!=sb[k].data_ptr()and torch.equal(sa[k],sb[k])
restored=trajectory(b,ob,rb,s['order'],s['cursor'],s['history'],s['uniqueUpdates']);assert digest(restored)==before
restore_extra_rng(obj['extra_rng']);assert digest(extra_rng())==digest(obj['extra_rng'])
steps=sorted(set(float(x['step'])for x in ob.state.values()))
r=dict(inherited_full_state_digest=before,source_active_cursor=obj['active_cursor'],source_model_unique_updates=s['uniqueUpdates'],adam_steps=steps,learning_rates=[g['lr']for g in ob.param_groups],parameters=sum(p.numel()for p in b.parameters()),restored_trajectory_exact=True,model_and_Adam_tensor_storage_independent=True,global_python_numpy_rng_exact=True,torch_and_private_python_rng_exact=True,optimizer_updates=0,update_resume_validation='pending fixed TRAIN schedule',seconds=time.monotonic()-started,max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(P/'STATE_PREFLIGHT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
