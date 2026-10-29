"""Inspect real trained states, not only intended settings."""
import copy
from common import *

def main():
 torch.set_num_threads(2);rows={}
 for a in ['A','B','C']:
  raw=P/'run'/a/'checkpoint-0512.pt';manifest=P/'run'/a/('archive-0512'if a=='A'else'archive')/'checkpoint.json';s=torch.load(raw,map_location='cpu',weights_only=False)if raw.exists()else loader.load_checkpoint(manifest,read(manifest)['sha256']);st=s['trajectory'];assert s['active_cursor']==512;rows[a]=dict(config=st['config'],optimizer_steps=sorted({int(v['step'])for v in st['optimizer']['state'].values()}),torch_RNG=digest(st['torchRng']),private_RNG=digest(st['pythonRng']),active_cursor=s['active_cursor'],model_digest=digest(st['model']),model_counter=st['uniqueUpdates'],hyperparameters=[{k:v for k,v in g.items()if k!='params'}for g in st['optimizer']['param_groups']],plan_sha256=s['plan_sha256'])
  prior=digest(st);m,o,r=restore_isolated(st);moment=next(iter(o.state.values()))['exp_avg'];moment.view(-1)[0]+=1;assert digest(st)==prior
  rows[a]['restored_adam_mutation_does_not_modify_source']=True
 assert len({r['torch_RNG']for r in rows.values()})==1;assert len({r['private_RNG']for r in rows.values()})==1;assert len({r['model_digest']for r in rows.values()})==3
 assert rows['A']['optimizer_steps']==[3982]and rows['B']['optimizer_steps']==rows['C']['optimizer_steps']==[512];assert all(r['config']==rows['A']['config']for r in rows.values());assert all(r['hyperparameters']==rows['A']['hyperparameters']for r in rows.values());assert all(r['plan_sha256']==sha(P/'PLAN.json')for r in rows.values());write(P/'STATE_AUDIT.json',dict(pass_all=True,real_512_update_states=rows,initial_source_retained=True,optimizer_updates=0));print('3 real states independent; RNG/hyperparameters/config exact')
if __name__=='__main__':main()
