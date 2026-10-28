"""Same grounded inputs, one-factor full CE versus response CE; no arm aliasing."""
import argparse,copy,hashlib,importlib.util,json,math,os,pathlib,shutil,subprocess,sys
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))
import torch
from core import restore,trajectory,digest,exact,causal_ce,clip_grad_accurate

def batch(rows,arm):
 x=torch.zeros((len(rows),256),dtype=torch.long);y=torch.full_like(x,-100);presented=0;reply=0
 for i,r in enumerate(rows):
  s=r['sequence'];n=len(s)-1;assert n<=256 and s[-1]==2 and s[r['answer_start']-1]==4;x[i,:n]=torch.tensor(s[:-1]);y[i,:n]=torch.tensor(s[1:]);presented+=n;reply+=len(r['answer_ids'])
  if arm=='response':y[i,:r['answer_start']-1]=-100
 return x,y,{'presented_targets':presented,'supervised_targets':int(y.ne(-100).sum()),'response_targets_including_EOS':reply}
def save(p,obj):
 with p.with_suffix('.pending').open('wb')as f:torch.save(obj,f);f.flush();os.fsync(f.fileno())
 os.replace(p.with_suffix('.pending'),p);fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
def ledger(p,d):
 with p.open('a')as f:f.write(json.dumps(d)+'\n');f.flush();os.fsync(f.fileno())
def main():
 a=argparse.ArgumentParser();a.add_argument('--child',choices=['full','response']);args=a.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);plan=json.loads((H/'PLAN.json').read_text());assert hashlib.sha256((H/'data.json').read_bytes()).hexdigest()==plan['data_sha256'];assert hashlib.sha256((H/'train.py').read_bytes()).hexdigest()==plan['train_code_sha256'];data=json.loads((H/'data.json').read_text())['train'];assert len(data)>=2048;out=H/'run';out.mkdir(exist_ok=True)
 s=importlib.util.spec_from_file_location('own_loader',V/'foundation-data/research/zero_update_preflight.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);base=m.load_checkpoint(V/'epoch1/medium/archive/checkpoint.pt.chunks.json',plan['initial_checkpoint_sha256']);initial_digest=digest(base['trajectory']);settings=json.loads((V/'PLAN.json').read_text())['training']
 for arm in ([args.child]if args.child else['full','response']):
  if args.child:saved=torch.load(out/(arm+'-16.pt'),map_location='cpu',weights_only=False);state=saved['trajectory'];trace=saved['trace'][:];start=16;end=32
  else:
   if (out/(arm+'-512.pt')).exists():raise ValueError('No overwrite')
   assert shutil.disk_usage(out).free>3*135802269+32*1024**2;state=base['trajectory'];trace=[];start=0;end=512
  model,opt,rng=restore(copy.deepcopy(state),settings);assert all(int(s['step'])==3470+start for s in opt.state_dict()['state'].values());assert all(g['lr']==3e-5 for g in opt.param_groups)
  if not args.child:assert digest(trajectory(model,opt,rng,state['order'],state['cursor'],state['history'],3470))==initial_digest
  for step in range(start,end):
   rows=data[4*step:4*step+4];x,y,dose=batch(rows,arm);opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);assert torch.isfinite(loss);loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters()if p.requires_grad);norm=float(clip_grad_accurate(model.parameters(),1.));assert math.isfinite(norm)
   ledger(out/'updates.jsonl',dict(arm=arm,step=step+1,replay=bool(args.child),event='intent'));opt.step();ledger(out/'updates.jsonl',dict(arm=arm,step=step+1,replay=bool(args.child),event='completed'));opt.zero_grad(set_to_none=True)
   trace.append(dict(step=step+1,loss=float(loss.detach()),gradient_norm=norm,**dose))
   if step+1 in [16,32,512]:
    st=trajectory(model,opt,rng,state['order'],state['cursor'],state['history'],3471+step);obj=dict(modelName='medium',trajectory=st,trace=trace,active_cursor=step+1,arm=arm,contract='grounded-objective-v1')
    if args.child:
     (out/(arm+'-replay.json')).write_text(json.dumps({'digest':digest(st),'trace':trace},indent=2)+'\n');os._exit(73)
    save(out/(arm+'-'+str(step+1)+'.pt'),obj)
   if step+1==32 and not args.child:
    reference={'digest':digest(st),'trace':trace[:]};proc=subprocess.run([sys.executable,str(H/'train.py'),'--child',arm],cwd=V.parents[2]);assert proc.returncode==73;assert exact(json.loads((out/(arm+'-replay.json')).read_text()),reference);(out/(arm+'-16.pt')).unlink();(out/(arm+'-resume-audit.json')).write_text(json.dumps({'steps16_to32_exact':True,'replay_updates':16,'process_exit':73,'initial_state_isolated':True},indent=2)+'\n')
   if (step+1)%32==0:print(arm,step+1,'loss',round(float(loss.detach()),4),flush=True)
  assert digest(base['trajectory'])==initial_digest
 events=[json.loads(l)for l in(out/'updates.jsonl').open()];n=sum(e['event']=='completed'for e in events);assert n==1056;(out/'receipt.json').write_text(json.dumps({'actual_optimizer_updates':n,'retained_updates':1024,'replay_updates':32,'retained_per_arm':512,'new_pairs_per_arm':2048,'pair_repetition_within_arm':0,'stages':[32,512]},indent=2)+'\n')
if __name__=='__main__':main()
