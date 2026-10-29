"""Freeze a single no-repeated-target pass and three controlled initialization arms."""
import collections,random,math
from common import *
rows=gzrows(P/'corpus.jsonl.gz');tr=[r for r in rows if r['split']=='train'];allnew=read(P/'NEW_DEV_SOURCES.json');valid=[0,1,2,4,9,12,14,15,17];dev=[allnew[i]for i in valid]
# Source reviews before any output. No corpus TRAIN or prior DEV is moved into evaluation.
write(P/'NEW_DEV_REVIEW.json',dict(reviewed=20,valid_indices=valid,excluded={str(i):'specialist ungrounded/dated/medical/graphic or reference-dependent passage; excluded before any generation'for i in range(20)if i not in valid},independent_native_human=False,previously_seen_now=True,not_sealed_TEST=True))
# Reuse PR102 approved independent whole-paragraph boundary contract only at identical source positions.
short={r['id']for r in read(N/'paragraphs.json')if r['split']=='train'} if isinstance(read(N/'paragraphs.json'),list) else set()
# Read schema defensively without changing source text.
if not short:
 obj=read(N/'paragraphs.json');short={r['id']for r in (obj['train']if isinstance(obj,dict)else obj)if r['split']=='train'}
new_short=0
for r in tr:
 prior_id=r['provenance']['id']+':paragraph'+str(r['paragraph_ordinal'])
 if r['source']!='jaquad'and prior_id in short and len(r['body_tokens'])<=240:
  r['tokens']=[1]+r['body_tokens']+[2];r['BOS']=r['EOS']=True;r['boundary_contract']='PR102 original whole paragraph standalone task, not page end';new_short+=1
# Keep all 20 source records for audit, but only valid nine are evaluation outputs.
gzipwrite(P/'corpus.jsonl.gz',tr+[r for r in rows if r['split']=='dev'])
windows=[]
for r in tr:
 seq=r['tokens']
 for start in range(0,len(seq)-1,256):
  s=seq[start:start+257]
  if len(s)<2:continue
  windows.append(dict(id=r['id']+'@'+str(start),unit_id=r['id'],start=start,tokens=s,source=r['source'],component=r['component']))
random.Random(31029).shuffle(windows);batches=[windows[i:i+4]for i in range(0,len(windows),4)];counts=[sum(len(w['tokens'])-1 for w in b)for b in batches];comparison=512
assert len(batches)>comparison and sum(counts)>1_800_000
with(P/'schedule.json.gz').open('wb')as f:
 with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0)as z:z.write(json.dumps(dict(batches=batches),ensure_ascii=False,separators=(',',':')).encode())
cases=[]
for i,r in enumerate(dev):
 body=r['body_tokens'];n=min(32,max(12,len(body)//5));prefix=([1]if r['BOS']else[])+body[:n];assert len(prefix)+128<=256
 cases.append(dict(id='new-family-'+str(i),source_id=r['id'],component=r['component'],title=r['title'],prefix=prefix,prefix_text=b''.join(bytes.fromhex(read(V/'data/tokenizer.json')['bytes'][x])for x in prefix if x>=6).decode('utf8','replace'),reference_suffix=body[n:],boundary_contract='source BPE exact prefix; source excerpt not assumed complete document',requirement='Coherent natural Japanese continuation on prefix topic, no loop, not empty/ack; strict full output judged separately from EOS'))
write(P/'DEV_PROTOCOL.json',dict(cases=cases,new_family_count=len(cases),old24=read(H/'TOKEN_BOUNDARY_PROTOCOL.json'),roles='all exposed research DEV; no sealed TEST or independent native human',greedy=dict(full_vocabulary=True,max_new=128,no_rolling=True,no_repair=True)))
plan=dict(series='Japanese pretraining scale v1',arms={'A':dict(model='inherited3470',adam='inherited3470'),'B':dict(model='inherited3470',adam='zero'),'C':dict(model='fresh own architecture seed31028',adam='zero')},initial_sha256=read(V/'epoch1/medium/archive/checkpoint.pt.chunks.json')['sha256'],config=read(V/'PLAN.json')['models']['medium'],comparison_updates=comparison,comparison_targets=sum(counts[:comparison]),full_pass_updates=len(batches),full_pass_targets=sum(counts),unique_body_tokens=sum(len(r['body_tokens'])for r in tr),new_vs_PR101_tokens=sum(len(r['body_tokens'])for r in tr if r['new_vs_PR101']),batch=4,context=256,lr=dict(peak=2e-4,warmup=128,end=3e-5,policy='common linear warmup then cosine across full fixed one-pass schedule; reset LR schedule is new shared research condition'),adam=dict(type='AdamW',betas=[.9,.999],eps=1e-8,weight_decay=.05),clipping=1.,fp32=True,training_torch_rng='exact inherited3470 torchRng after all model/Adam initialization',sampler_seed=31029,checkpoints=dict(comparison=512,continuation_every=512,terminal=len(batches),rolling_every=128),selection='At common512 choose highest strict prose success over old24+new9; then lowest repeat count; then lowest aggregate teacher DEV NLL; ties A,B,C order. All-zero success permits exactly ONE full admitted-data pass as undertraining diagnosis, not capability success. DEV selection bias explicit.',success='old strict gate unchanged; exploratory improvement requires>=4/24 strict old prose, >=2 more than inherited initial, and harmful repeats<=initial0; new9 separate and necessary qualitative check. EOS or NLL alone insufficient.',continuation_gate='finite losses/gradients, exact resume, no safety/data failure, valid storage; all-zero comparison can proceed to ONE corpus pass; no repeated epoch; if later NLL improves but repetition increases relative previous milestone, record regression and do not extend beyond fixed pass',stop='nonfinite, ambiguous optimizer intent, mismatched source SHA, resume discrepancy, free disk below600MiB; save or preserve last atomic state; no fabricated count',response_gate='Only if strict natural prose materially improves without repeated/irrelevant replacement; else no response phase',limits=dict(no_subagents=True,paid_resources=False,public_replacement=False,sealed_TEST=False,maximum_extra_epochs=0),EOS_teachers=sum(w['tokens'][1:].count(2)for w in windows),BOS_teachers=sum(w['tokens'][1:].count(1)for w in windows),completed_short_units=new_short)
inputs=[P/'corpus.jsonl.gz',P/'schedule.json.gz',P/'DEV_PROTOCOL.json',P/'QUALITY_REVIEW.json',V/'data/tokenizer.json',ROOT/'training/language/model.py',V/'core.py']
plan['input_sha256']={str(p.relative_to(ROOT)):sha(p)for p in inputs};write(P/'PLAN.json',plan);print({k:plan[k]for k in ['comparison_targets','full_pass_updates','full_pass_targets','unique_body_tokens','new_vs_PR101_tokens','EOS_teachers','BOS_teachers','completed_short_units']})
