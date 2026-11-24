"""Read-only paired-state checks at fixed1000/5000; never change the trainer."""
import pathlib,json,hashlib,io,sys,time,datetime,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round33';repo=R.parents[2];sys.path.insert(0,str(R));from checkpoint_chunks import pack
from prefix_selection import load_selector
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();torch.set_num_threads(1)
plan={1000:P/'execution/retained-selected-1000/checkpoint.pt.chunks.json',5000:P/'execution/retained-progress-5000/checkpoint.pt.chunks.json'}
selector=load_selector(R/'human-turn-token-boundaries.json',read(R/'multiview/tokenizer.json'),read(R/'multiview/train.index.json'),read(R/'policy.json')['humanNegativePrefix']['featureMapSha256'],sha(R/'multiview/tokenizer.json'),sha(R/'multiview/train.index.json'),sha(R/'sources/documents.jsonl'))
def trace(path,step):
 raw=path.read_text();out=[];lines=raw.splitlines()
 for i,line in enumerate(lines):
  try:x=json.loads(line)
  except json.JSONDecodeError:
   if i==len(lines)-1 and not raw.endswith('\n'):continue
   raise
  if x['step']<=step:out.append(x)
 return out
def parent_state(manifest):
 info=read(manifest);parts=[]
 for row in info['chunks']:
  data=(manifest.parent/row['path']).read_bytes();assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256'];parts.append(data)
 data=b''.join(parts);assert len(data)==info['bytes']and hashlib.sha256(data).hexdigest()==info['sha256'];return torch.load(io.BytesIO(data),map_location='cpu',weights_only=False),info['sha256']
for target,manifest in plan.items():
 O=E/f'retained-paired-{target}';report=O/'snapshot.json'
 if report.exists():continue
 while True:
  time.sleep(10)
  try:
   log=E/'train.log';lines=log.read_text().splitlines();events=[json.loads(s)for s in lines if s.startswith('{')];last=events[-1].get('step',0)
   if last<target:continue
   raw=(R/'continue-10000/checkpoint.pt').read_bytes();new=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=False)
   if new['step']<target:continue
   if new['step']>target:raise ValueError(f'Missed exact checkpoint{target}; no score/state is invented')
   break
  except (FileNotFoundError,json.JSONDecodeError):continue
 old,oldsha=parent_state(manifest);assert old['step']==new['step']==target and old['config']==new['config']
 assert old['pythonRng']==new['pythonRng']and torch.equal(old['torchRng'],new['torchRng'])
 assert old['seen_tokens']==new['seen_tokens']and old['seen_bytes']==new['seen_bytes']
 assert old['optimizer']['param_groups']==new['optimizer']['param_groups']
 assert sorted({int(s['step'])for s in new['optimizer']['state'].values()})==[20000+target]
 for a,b in zip(old['history'],new['history'],strict=True):assert a['step']==b['step']and a.get('seenTargetTokens',0)==b.get('seenTargetTokens',0)and a.get('seenTargetUtf8Bytes',0)==b.get('seenTargetUtf8Bytes',0)
 ot,nt=trace(P/'continue-10000/training-rollouts.jsonl',target),trace(R/'continue-10000/training-rollouts.jsonl',target);assert len(ot)==len(nt)==target//10;changed=human=0
 for a,b in zip(ot,nt,strict=True):
  assert a['step']==b['step']and a['sourceRow']==b['sourceRow'];n=selector.length(a['sourceRow'],a['tokens'][0]);assert b['prefixLength']==n and b['tokens'][:n]==a['tokens'][:n];changed+=n!=a['prefixLength'];human+=a['sourceRow']['site']=='human-chat'
 weights_differ=any(not torch.equal(t,old['model'][k])for k,t in new['model'].items());assert weights_differ
 O.mkdir(exist_ok=True);cp=O/'checkpoint.pt';cp.write_bytes(raw);pack(cp)
 out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actualRetainedUpdates=target,selectedStep=new['beststep'],optimizerCounters=[20000+target],childCheckpointSha256=hashlib.sha256(raw).hexdigest(),controlCheckpointSha256=oldsha,torchAndPrivatePythonRngExactlyMatch=True,positiveTargetTokensExactlyMatch=new['seen_tokens'],positiveTargetBytesExactlyMatch=new['seen_bytes'],optimizerGroupsExactlyMatch=True,allRecordedFirstNegativeRowsAndOriginalTokenPrefixesMatch=True,checkedNegativeCalls=len(nt),humanNegativeCalls=human,changedHumanPrefixes=changed,allChangedPrefixesFollowFrozenPolicy=True,modelWeightsActuallyDiffer=True,notModelWeightsEqualityClaim=True,noOptimizerByDiagnostic=True,noConditionOrSelectionChange=True,notNewTest=True,codeSha256=sha(pathlib.Path(__file__)))
 report.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True);del old,new,raw
