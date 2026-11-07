"""Freeze budgets, source selection, evaluands and failure criteria before optimizer calls."""
from common import *
import collections
corpus=gzrows(D/'corpus.jsonl.gz');sc=json.load(gzip.open(D/'schedule.json.gz','rt'));batches=sc['batches'];targets=[sum(len(w['tokens'])-1 for w in b)for b in batches];n=next(i for i in range(1,len(targets)+1)if sum(targets[:i])>=1_500_000);mid=next(i for i in range(n+1,len(targets)+1)if sum(targets[:i])>=3_200_000)
proto=read(P/'DEV_PROTOCOL.json');cases=[dict(panel='old24',**r)for r in proto['old24']['cases']]+[dict(panel='oldNew9',**r)for r in proto['cases']]+read(D/'NEW_DEV_SOURCES.json')
tr=[r for r in corpus if r['split']=='train'];probes=[]
for source in ['jaquad','jawikibooks','realpersona','jma']:
 r=min([r for r in tr if r['source']==source],key=lambda r:rank('probe|'+r['id']));t=r['tokens'];cut=24;probes.append(dict(panel='train4',id=r['id'],prefix=t[:cut],reference=t[cut:],source=source))
cases+=probes;devwindows=[]
for r in corpus:
 if r['split']=='dev':
  for j in range(0,len(r['tokens'])-1,256):devwindows.append(dict(panel='JMA',id=r['id']+'@'+str(j),tokens=r['tokens'][j:j+257]))
for r in json.load(gzip.open(H/'schedule.json.gz','rt'))['dev']:devwindows.append(dict(panel='old_prose',**r))
# Preserve PR103 new-family NLL exactly the same valid source IDs.
ids={r['source_id']for r in proto['cases']}
for r in gzrows(P/'corpus.jsonl.gz'):
 if r['id']in ids:
  for j in range(0,len(r['tokens'])-1,256):devwindows.append(dict(panel='old_new_family',id=r['id']+'@'+str(j),tokens=r['tokens'][j:j+257]))
write(D/'EVALUATION.json',dict(cases=cases,dev_windows=devwindows,decode=dict(full_vocabulary=True,greedy=True,max_new=128,rolling=False,repair=False),all_DEV=True,sealed_TEST_used=False,independent_human_evaluation=False,semantic_rubric=read(P/'EVALUATION_RUBRIC.json'),new_DEV_scope='three entirely reserved JMA FAQ pages; not independent authors, may share broad weather topic; explicit source-family but not semantic-independence proof'))
health=[]
for r in sorted([r for r in tr if r['source']=='jma'and 70<=len(r['body_tokens'])<=140],key=lambda r:rank('health|'+r['id']))[:3]:
 cut=24
 while True:
  try:b''.join(bytes.fromhex(read(V/'data/tokenizer.json')['bytes'][t])for t in r['body_tokens'][:cut]).decode('utf8','strict');break
  except UnicodeError:cut+=1
 health.append(dict(id=r['id'],text=r['text'],tokens=[1]+r['body_tokens']+[2],prefix=[1]+r['body_tokens'][:cut],reference=r['body_tokens'][cut:]+[2]))
assert len(health)==3 and len({tuple(r['prefix'])for r in health})==3
write(D/'HEALTH_SOURCES.json',health)
plan=dict(series='diverse-foundation-v1',initial_source='medium3470 before all experimental pretraining',initial_sha256=read(V/'epoch1/medium/archive/checkpoint.pt.chunks.json')['sha256'],arms=dict(A='old3470 model + zero Adam',B='own fresh seed41029 model + zero Adam'),optimizer_rationale='PR103 reset alone did not fix generation; reset BOTH here to isolate model weights/history (PR103 B/C design). Not comparison of inherited Adam versus fresh Adam.',training_rng='exact inherited3470 torch/private RNG after all model construction; initialization draws isolated',sampler_seed=41030,model=read(V/'PLAN.json')['models']['medium'],BPE=3997,context=256,batch=4,loss='all genuine causal teacher positions; original human role/EOS targets retained; no response CE or auxiliary changes',lr=dict(peak=2e-4,end=3e-5,warmup=128,schedule='same full-pass linear warmup/cosine'),adam=dict(type='AdamW',betas=[.9,.999],eps=1e-8,weight_decay=.05),clipping=1.,comparison_updates=n,comparison_targets=sum(targets[:n]),midpoint_updates=mid,midpoint_targets=sum(targets[:mid]),full_pass_updates=len(batches),full_pass_targets=sum(targets),body_tokens=sum(len(r['body_tokens'])for r in tr),maximum_main_epochs=1,checkpoint_retention='A/B comparison, chosen arm midpoint and terminal; rolling every128. Other snapshots replaced only after atomic full-state success. Archive chunks <=32MiB.',selection='Compare strict semantic old24 + oldNew9 + newJMA. If A has more strict full successes, select A; if B has more select B. If tied, select B fresh to answer preregistered fresh-learning question rather than lock old prior by NLL alone. NLL reported separately; not capability. Chosen arm gets remaining unique one-pass corpus only.',success='Exploratory material language improvement requires strict old prose>=4/24 and improvement>=2, >=3/12 new FAQ, harmful repetition reduction, full-output reading, no unsupported topic replacement. Unchanged formal17/13/9/Pareto gates NOT claimed passed.',stop='nonfinite, source SHA mismatch, ambiguous intent, restart mismatch, disk<600MiB: stop/preserve last checkpoint. NLL-only improvement permits initially frozen one-pass undertraining diagnosis, never extra epochs or response phase. If new established semantic gains regress>=2 cases or harmful repeats increase>=4, pause before next stage for recorded analysis.',response_gate='Only after genuine unknown-family base-generation gains and no substantial regression; otherwise no response training',health=dict(max_updates=384,check_every=64,lr=.0003,loss='full causal',three_distinct_prefixes=True,criterion='all3 exact continuation including genuine EOS; memorization only, not generalization'),limits=dict(subagents=False,paid_resources=False,sealed_TEST=False,public_replacement=False,merge=False),source_history='A already saw RP during its old2.82Mtarget first epoch; B saw none. Equal additional targets is NOT equal cumulative training.',free_bytes_at_freeze=__import__('shutil').disk_usage(D).free)
inputs=[D/'corpus.jsonl.gz',D/'schedule.json.gz',D/'EVALUATION.json',D/'HEALTH_SOURCES.json',D/'QUALITY_REVIEW.json',D/'RIGHTS.md',V/'data/tokenizer.json',ROOT/'training/language/model.py',V/'core.py',D/'common.py',D/'state.py',D/'train.py',D/'preflight.py',D/'health.py',D/'evaluate.py']
plan['input_sha256']={str(p.relative_to(ROOT)):sha(p)for p in inputs};write(D/'PLAN.json',plan);print({k:plan[k]for k in ['body_tokens','comparison_updates','comparison_targets','full_pass_updates','full_pass_targets','midpoint_updates']})
