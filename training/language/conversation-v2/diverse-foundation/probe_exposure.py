"""TRAIN split membership does not imply that a particular continuation was updated at a midpoint."""
from common import *
plan=read(D/'PLAN.json');cases=[r for r in read(D/'EVALUATION.json')['cases']if r['panel']=='train4'];batches=json.load(gzip.open(D/'schedule.json.gz','rt'))['batches'];out={}
for n in [0,plan['comparison_updates'],plan['midpoint_updates'],plan['full_pass_updates']]:
 positions={r['id']:set()for r in cases}
 for b in batches[:n]:
  for w in b:
   if w['unit_id']in positions:positions[w['unit_id']].update(range(w['start']+1,w['start']+len(w['tokens'])))
 result=[]
 for r in cases:
  gold=r['reference'][:128]
  if 2 in gold:gold=gold[:gold.index(2)+1]
  expected=set(range(len(r['prefix']),len(r['prefix'])+len(gold)));result.append(dict(id=r['id'],source=r['source'],expected_positions=len(expected),actually_updated_reference_positions=len(expected&positions[r['id']]),all_expected_positions_updated=expected<=positions[r['id']],A_prior_history='Already exposed in original RP epoch'if r['source']=='realpersona'else'no corpus prose in inherited3470'))
 out[str(n)]=result
write(D/'TRAIN_PROBE_EXPOSURE.json',dict(milestones=out,note='Common1983 TRAIN probes may include not-yet-updated reference positions. Only terminal full-pass guarantees every retained position. These are not independent DEV and main no-match alone does not prove inability to memorize.'))
