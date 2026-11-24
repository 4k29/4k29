"""Gated exploratory runner; current protocol does not authorize optimizer updates.

Writes separate atomic full states for each arm. Full post-update replay and
language evaluation remain prerequisites before this runner can be approved.
"""
import argparse,array,hashlib,importlib.util,json,os,pathlib,shutil,sys,math
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan-sha256',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 raw=(H/'EXPERIMENT.json').read_bytes();plan=json.loads(raw)
 if hashlib.sha256(raw).hexdigest()!=a.plan_sha256:raise ValueError('Plan SHA mismatch')
 if plan['optimizer_updates_authorized']is not True:raise PermissionError('Current study is No-Go; optimizer updates prohibited')
 if a.output.exists():raise ValueError('Fresh output directory required; explicit resume procedure must be separately audited')
 if shutil.disk_usage(a.output.parent).free<3*135802269+32*1024**2:raise OSError('Insufficient atomic multi-arm checkpoint reserve')
 import torch
 from core import restore,trajectory,pack,causal_ce,clip_grad_accurate
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 s=importlib.util.spec_from_file_location('own_load',V/'foundation-data/research/zero_update_preflight.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 initial=json.loads((V/'foundation-data/research/PREFLIGHT_PLAN.json').read_text());repo=V.parents[2];saved=m.load_checkpoint(repo/initial['checkpointManifestPath'],initial['checkpointSha256']);state=saved['trajectory'];settings=json.loads((V/'PLAN.json').read_text())['training']
 meta=json.loads((V/'data/data.json').read_text());values=array.array('I');source=repo/meta['trainTokensPath'];assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['trainTokensSha256'];values.frombytes(source.read_bytes());assert hashlib.sha256((H/'schedule.json').read_bytes()).hexdigest()==plan['schedule_sha256'];schedule=json.loads((H/'schedule.json').read_text())['rows'];assert len(schedule)==plan['retained_updates_per_arm'];a.output.mkdir()
 for arm in ['control','treatment']:
  model,opt,rng=restore(state,settings);assert all(g['lr']==plan['learning_rate']for g in opt.param_groups);history=list(state['history']);trace=[]
  for row in schedule:
   opt.zero_grad(set_to_none=True);x,y,dose=pack(values,meta['trainWindows'],row[arm+'_window_ids'],model.config['vocabulary']);loss=causal_ce(model(x),y);loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters() if p.requires_grad);norm=float(clip_grad_accurate(model.parameters(),1.));assert math.isfinite(norm);opt.step();trace.append(dict(step=row['step'],loss=float(loss.detach()),gradient_norm=norm,**dose));opt.zero_grad(set_to_none=True)
   payload={'trajectory':trajectory(model,opt,rng,state['order'],state['cursor'],history,3470+row['step']),'modelName':'medium','allocation_step':row['step'],'allocation_arm':arm,'schedule_sha256':plan['schedule_sha256'],'actual_optimizer_updates':row['step'],'trace':trace,'legacy_sampler_frozen_for_provenance':True,'active_sampler':'fixed allocation schedule; cursor is allocation_step'}
   with(a.output/'pending.tmp').open('wb')as f:torch.save(payload,f);f.flush();os.fsync(f.fileno())
   os.replace(a.output/'pending.tmp',a.output/(arm+'.pt'));fd=os.open(a.output,os.O_RDONLY);os.fsync(fd);os.close(fd)
if __name__=='__main__':main()
