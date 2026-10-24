"""Exercise the untrained candidate on every existing TRAIN row, no model."""
import json,pathlib,sys,hashlib,collections,numpy as np,torch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from utterance_end_objective import eligible_mask
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution/prospective-eos-objective'
sys.path.insert(0,str(R));from train import pack
info=json.loads((R/'multiview/train.index.json').read_text());ends=json.loads((R/'human-turn-token-boundaries.json').read_text())['boundariesByUnit'];values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');torch.set_num_threads(1);rng=torch.get_rng_state().clone();count=collections.Counter();groups=collections.defaultdict(list)
for row in info['rows']:groups[next(w for w in (64,128,256)if row['length']-1<=w)].append(row)
for width,rows in groups.items():
 for start in range(0,len(rows),64):
  batch=rows[start:start+64];x,y=pack(batch,values,width);before=y.clone();mask=eligible_mask(batch,y,ends)
  assert torch.equal(y,before)
  for i,row in enumerate(batch):
   count['checkedRows']+=1
   if row['site']!='human-chat':assert not mask[i].any();count['nonhumanRowsExactZero']+=1
   else:
    count['humanRows']+=1;count['eligibleView'+str(row['variant'])]+=int(mask[i].sum())
    # Independent direct index criterion over each original target position.
    expected=torch.tensor([j>=row['prefixLength']-1 and j<row['length']-1 and int(y[i,j])==16 and row['start']+j+2 in ends[row['unit']] for j in range(width)])
    assert torch.equal(mask[i],expected)
assert torch.equal(rng,torch.get_rng_state());assert count['checkedRows']==len(info['rows'])
report=dict(counts=dict(count),allRowsMatchIndependentPositionCriterion=True,positiveLabelsUnmodified=True,nonhumanAuxiliaryMaskAlwaysZero=True,rngUnchanged=True,noModelOrOptimizerUsed=True,noHeldoutOpened=True,noControlRound39FilesModified=True,integratedRound40ObjectiveSha256=hashlib.sha256((R/'utterance_end_objective.py').read_bytes()).hexdigest(),actualNewRoundUpdates=0,notLanguageEvidence=True,codeSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest())
(R/'execution/eos-full-training-mask-preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
