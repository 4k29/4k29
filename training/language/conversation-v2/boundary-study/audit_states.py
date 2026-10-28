from eval_runtime import *

def main():
 torch.set_num_threads(2);base=initial()['trajectory'];source=digest(base);rows={};rng=[]
 for name in ['control','boundary','clip5']:
  obj=snapshot(name);s=obj['trajectory'];before=digest(s);model,opt,_=restore_isolated(s);v=next(iter(opt.state.values()))['exp_avg'];v.view(-1)[0]+=1;assert digest(s)==before and digest(base)==source;steps={int(v['step'])for v in s['optimizer']['state'].values()};assert steps=={3982}and obj['active_cursor']==512;r=(digest(s['torchRng']),digest(s['pythonRng']));rng.append(r);rows[name]=dict(full_trajectory_digest=before,model_digest=digest(s['model']),config_matches_original=s['config']==base['config'],adam_states=len(s['optimizer']['state']),unique_updates=s['uniqueUpdates'],active_cursor=obj['active_cursor'],source_adam_independent=True,rng_digest=r)
 assert len(set(rng))==1;assert len({r['model_digest']for r in rows.values()})==3;write(N/'STATE_AUDIT.json',dict(states=rows,endpoint_RNG_same=True,old_source_untouched=True,optimizer_updates=0));print('Three states isolated, exact512-step RNG/counter and source identity verified')
if __name__=='__main__':main()
