"""Real model audit without optimizer calls. Does not certify language ability."""
import copy,gzip,json,math,resource,shutil,time
from mixed_runtime import H,torch,initial,restore_isolated,digest,pack,causal_ce,clip_grad_accurate
def main():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);base=initial()['trajectory'];before=digest(base);model,opt,rng=restore_isolated(base);schedule=json.load(gzip.open(H/'mixed-schedule.json.gz','rt'));rows=[]
 for i in range(4):
  x,y=pack(schedule['batches'][i]);tick=time.monotonic();opt.zero_grad(set_to_none=True);logits=model(x);loss=causal_ce(logits,y);ref=torch.nn.functional.cross_entropy(logits.reshape(-1,3997),y.reshape(-1),ignore_index=-100);assert abs(float(loss.detach()-ref.detach()))<3e-6;loss.backward();ps=list(model.parameters());assert all(torch.isfinite(p.grad).all()for p in ps);norm=float(clip_grad_accurate(ps,1));post=sum(float(p.grad.double().square().sum())for p in ps)**.5;assert post<=1+2e-5 and math.isfinite(norm);rows.append(dict(targets=int(y.ne(-100).sum()),seconds=time.monotonic()-tick,CE=float(loss.detach()),independent_CE=float(ref.detach()),gradient_norm=norm,postclip_norm=post))
 assert digest(base)==before and all(int(s['step'])==3470 for s in opt.state.values())
 speed=sum(r['targets']for r in rows)/sum(r['seconds']for r in rows)
 result=dict(actual_optimizer_updates=0,inherited_unique_updates=base['uniqueUpdates'],Adam_states=len(opt.state),all_Adam_steps3470=True,initial_state_untouched=True,modelTraining=base['modelTraining'],parameters=sum(p.numel()for p in model.parameters()),config=model.config,lr=[g['lr']for g in opt.param_groups],torch=torch.__version__,threads=2,measured_forward_backward_targets_per_second=speed,estimated_one_pass_seconds_with20percent_step_overhead=schedule['targets']/speed*1.2,disk_free_bytes=shutil.disk_usage(H).free,maximum_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,rows=rows)
 (H/'PREFLIGHT_MIXED.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items()if k not in ['rows','config']})
if __name__=='__main__':main()
