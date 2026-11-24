"""Post-run, zero-update state comparison; source state never shared with Adam."""
import json
from runtime import H,torch,initial,snapshot,digest,restore_isolated

def main():
 torch.set_num_threads(2);base=initial()['trajectory'];before=digest(base);rows={};rngs={}
 for name in ['foundation','foundation-mixed','foundation-lr','qa-only','qa-rehearsal']:
  s=snapshot(name);st=s['trajectory'];m,opt,_=restore_isolated(st);digest_before=digest(st)
  # Mutating one restored moment is an explicit, zero-step alias test.
  value=next(iter(opt.state.values()))['exp_avg'];value.view(-1)[0]+=1
  assert digest(st)==digest_before,'Restoring aliased source Adam'
  assert digest(base)==before;steps={int(x['step'])for x in st['optimizer']['state'].values()};assert steps=={st['uniqueUpdates']};assert s['active_cursor']==len(s['trace'])
  rngs[name]=(digest(st['torchRng']),digest(st['pythonRng']))
  rows[name]=dict(unique_updates=st['uniqueUpdates'],active_cursor=s['active_cursor'],adam_state_count=len(st['optimizer']['state']),adam_steps=list(steps),model_sha256=digest(st['model']),full_trajectory_sha256=digest(st),rng_sha256=rngs[name],config_identical_to_original=st['config']==base['config'],parameter_count=sum(p.numel()for p in m.parameters()),lr=[g['lr']for g in st['optimizer']['param_groups']],restored_adam_independent=True)
 assert rngs['foundation']==rngs['foundation-mixed']==rngs['foundation-lr'];assert rngs['qa-only']==rngs['qa-rehearsal'];assert len({rows[n]['model_sha256']for n in rows})==5
 (H/'STATE_AUDIT.json').write_text(json.dumps(dict(states=rows,foundation_same_endpoint_rng=True,response_same_endpoint_rng=True,source_initial_immutable=True,optimizer_updates=0,notes='Legacy sampler order/cursor preserved as provenance; active cursor indexes frozen explicit schedule. Same RNG does not imply equal learned models.'),indent=2)+'\n');print('Five isolated states, original config, exact endpoint RNGs and Adam steps verified')
if __name__=='__main__':main()
