"""Prepared retention comparison; requires a separate, explicitly fixed Go plan."""
import argparse,copy,gzip,json,math,os,shutil,subprocess,sys
from runtime import H,torch,snapshot,save,record,sha,restore_isolated,trajectory,digest,causal_ce,clip_grad_accurate
def batch(rows):
 x=torch.zeros((len(rows),256),dtype=torch.long);y=torch.full_like(x,-100)
 for i,r in enumerate(rows):
  s=r['sequence'];L=r['answer_start'];assert s==r['prefix']+r['answer_ids']and len(s)<=257;x[i,:len(s)-1]=torch.tensor(s[:-1]);y[i,L-1:len(s)-1]=torch.tensor(r['answer_ids'])
 return x,y
def main():
 p=argparse.ArgumentParser();p.add_argument('--replay',choices=['control','treatment']);a=p.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 plan=json.loads((H/'RESPONSE_PLAN.json').read_text());assert plan['training_authorized']is True;assert sha(H/'response-schedule.json.gz')==plan['schedule_sha256'];assert sha(H/'response_train.py')==plan['training_code_sha256'];out=H/'response-run';out.mkdir(exist_ok=True)
 if(out/'receipt.json').exists():raise SystemExit('Completed response comparison; refuse unrecorded repeats')
 if not a.replay:assert not(out/'updates.jsonl').exists(),'Explicit recovery required, never rerun both arms'
 source=H/'run'/(plan['initial_snapshot']+'.pt');source_sha=sha(source)if source.exists()else json.loads((H/'run'/plan['initial_snapshot']/'archive/checkpoint.json').read_text())['sha256'];assert source_sha==plan['initial_checkpoint_sha256'];base=snapshot(plan['initial_snapshot'])['trajectory'];assert base['uniqueUpdates']==plan['initial_unique_updates'];source_digest=digest(base);batches=json.load(gzip.open(H/'response-schedule.json.gz','rt'));N=len(batches);assert N==plan['updates_each']
 for arm in ([a.replay]if a.replay else['control','treatment']):
  state=torch.load(out/(arm+'-2.pt'),map_location='cpu',weights_only=False)if a.replay else dict(trajectory=base,trace=[],active_cursor=0);st=state['trajectory'];model,opt,rng=restore_isolated(st);start=2 if a.replay else 0;end=4 if a.replay else N;assert all(int(s['step'])==base['uniqueUpdates']+start for s in opt.state.values());trace=state['trace'][:]
  if not a.replay:assert digest(st)==source_digest and shutil.disk_usage(H).free>480*1024**2
  assert all(g['lr']==plan['lr']for g in opt.param_groups)
  for i in range(start,end):
   x,y=batch(batches[i][arm]);opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);assert torch.isfinite(loss);loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters());norm=float(clip_grad_accurate(model.parameters(),1));assert math.isfinite(norm);r=dict(step=i+1,loss=float(loss.detach()),gradient_norm_before_clip=norm,supervised_targets=int(y.ne(-100).sum()),presented_targets=sum(len(z['sequence'])-1 for z in batches[i][arm]))
   record(out/'updates.jsonl',dict(event='intent',arm=arm,replay=bool(a.replay),step=i+1));opt.step();record(out/'updates.jsonl',dict(event='completed',arm=arm,replay=bool(a.replay),step=i+1));opt.zero_grad(set_to_none=True);trace.append(r)
   if i+1 in [2,4]or(i+1)%64==0 or i+1==N:
    obj=dict(modelName='medium',contract='conditional-suffix-CE-QA-or-prose-v1',trajectory=trajectory(model,opt,rng,st['order'],st['cursor'],st['history'],base['uniqueUpdates']+i+1),trace=trace,active_cursor=i+1,source_snapshot=plan['initial_snapshot'],arm=arm)
    if a.replay:(out/(arm+'-replay.json')).write_text(json.dumps(dict(digest=digest(obj['trajectory']),trace=trace),indent=2)+'\n');os._exit(73)
    if i+1==2:save(out/(arm+'-2.pt'),obj)
    else:save(H/'run'/('qa-only.pt'if arm=='control'else'qa-rehearsal.pt'),obj)
    if i+1==4:
     proc=subprocess.run([sys.executable,str(H/'response_train.py'),'--replay',arm]);assert proc.returncode==73;assert json.loads((out/(arm+'-replay.json')).read_text())==dict(digest=digest(obj['trajectory']),trace=trace);(out/(arm+'-2.pt')).unlink()
   if(i+1)%64==0:print(arm,i+1,loss.item(),flush=True)
  assert digest(base)==source_digest,'PR99 Adam alias regression'
 calls=[json.loads(l)for l in(out/'updates.jsonl').read_text().splitlines()if json.loads(l)['event']=='completed'];receipt=dict(actual_optimizer_updates=len(calls),retained_updates=2*N,replayed_updates=sum(e['replay']for e in calls),updates_each=N,initial_state_identical_and_isolated=True)
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt,flush=True)
if __name__=='__main__':main()
