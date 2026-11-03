"""Frozen corpus/input/finite-gradient checks; no optimizer.step call."""
from study_runtime import *
from schedule import verify

def main():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);plan=read(P/'PLAN.json');psha=sha(P/'PLAN.json')
 for rel,h in plan['input_sha256'].items():assert sha(ROOT/rel)==h,rel
 assert read(P/'UPDATE_RESUME_AUDIT.json')['pass_all'];ensure_capacity();corpus,schedule=load_data();audits={a:verify(corpus,schedule['arms'][a])for a in ['A','B']};assert audits['A']['target_counts']==audits['B']['target_counts']==schedule['target_counts']
 assert all(r['family']!='osaka'and not str(r.get('source_url','')).startswith('https://www.city.osaka.lg.jp/')for r in corpus)
 obj=source();s=obj['trajectory'];before=digest(s);rows=[]
 for arm in ['A','B']:
  model,opt,rng=restore_isolated(s);restore_extra_rng(obj['extra_rng']);x,y=pack(windows(corpus,schedule['arms'][arm][0]));assert x.shape[1]<=256 and int(y.ne(-100).sum())==schedule['target_counts'][0]
  model.train();opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);loss.backward();norm=float(clip_grad_accurate(model.parameters(),1));assert math.isfinite(norm)and all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters())
  assert {int(v['step'])for v in opt.state.values()}=={6361};assert digest(s)==before
  model.eval();xx=x[:1].clone();yy=xx.clone();k=max(1,xx.shape[1]//2);yy[:,k:]=(yy[:,k:]+17)%3991+6
  with torch.inference_mode():
   a=model(xx);b=model(yy);error=float((a[:,:k]-b[:,:k]).abs().max());assert error<=2e-5
  rows.append(dict(arm=arm,targets=int(y.ne(-100).sum()),loss=float(loss.detach()),gradient_norm=norm,clipped=norm>1,causal_past_logit_max_error=error,batch_rows=x.shape[0],batch_width=x.shape[1],optimizer_step_unchanged=6361))
  del model,opt,rng
 assert digest(s)==before
 par=read(P/'PARAGRAPH_DEV_PROTOCOL.json');assert all(len(c['prefix'])+160<=256 and c['reference_new_sentences']>=2 for c in par['cases'])
 write(P/'PREFLIGHT.json',dict(pass_all=True,plan_sha256=psha,byte_recovery=read(P/'DATASET_AUDIT.json')['full_bpe_byte_recovery'],frozen_paragraph_DEV_cases=len(par['cases']),source_state_unchanged=True,gradient_audits=rows,actual_optimizer_calls=0,prior_execution_validation_optimizer_calls=6,old_formal_TEST_opened=False,persistent_free_bytes=shutil.disk_usage(DURABLE).free))
 print(json.dumps(read(P/'PREFLIGHT.json')))
if __name__=='__main__':main()
