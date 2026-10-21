"""Read-only retention of actual model/optimizer/RNG at fixed paired update counts."""
import pathlib,json,time,io,hashlib,torch,datetime,sys
R=pathlib.Path('/workspace/4k29/training/language/round35');E=R/'execution';P=R.parent/'round34';sys.path.insert(0,str(R));from checkpoint_chunks import pack
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();torch.set_num_threads(1);seen=set();last_stamp=None
for n in [200,1000,5000]:
 if (E/f'retained-paired-{n}/snapshot.json').exists():seen.add(n)
while len(seen)<3:
 p=R/'continue-10000/checkpoint.pt'
 if not p.exists():time.sleep(3);continue
 stamp=p.stat().st_mtime_ns
 if stamp==last_stamp:time.sleep(3);continue
 raw=p.read_bytes();last_stamp=stamp;b=torch.load(io.BytesIO(raw),weights_only=False,map_location='cpu');n=b['step']
 if n in [200,1000,5000] and n not in seen:
  loc=P/('execution/retained-progress-200'if n==200 else f'execution/retained-paired-{n}')/'checkpoint.pt';a=torch.load(loc,weights_only=False,map_location='cpu')
  assert a['step']==n and a['pythonRng']==b['pythonRng']and torch.equal(a['torchRng'],b['torchRng'])and a['seen_tokens']==b['seen_tokens']and a['seen_bytes']==b['seen_bytes']
  assert a['optimizer']['param_groups']==b['optimizer']['param_groups']and all(int(x['step'])==20000+n for x in b['optimizer']['state'].values())
  assert all(torch.isfinite(v).all()for v in b['model'].values())and all(torch.isfinite(t[k]).all()for t in b['optimizer']['state'].values()for k in ['exp_avg','exp_avg_sq'])
  d=E/f'retained-paired-{n}';d.mkdir();target=d/'checkpoint.pt';target.write_bytes(raw);pack(target)
  trace=[json.loads(s)for s in (R/'continue-10000/training-rollouts.jsonl').read_text().splitlines()if json.loads(s)['step']<=n];control=[json.loads(s)for s in (P/'continue-10000/training-rollouts.jsonl').read_text().splitlines()if json.loads(s)['step']<=n];assert len(trace)==len(control)==n//10
  for x,y in zip(control,trace,strict=True):assert x['step']==y['step']and x['sourceRow']==y['sourceRow']and x['prefixLength']==y['prefixLength']and x['tokens'][:x['prefixLength']]==y['tokens'][:y['prefixLength']]
  (d/'training-rollouts.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in trace))
  record=dict(actualUpdates=n,optimizerCounter=20000+n,checkpointSha256=sha(target),controlCheckpointSha256=sha(loc),samePositiveExposureCountsAndGlobalTorchAndPrivatePythonRngAsRound34=True,negativePrefixPolicyAndHistoriesExact=True,weightsAndMomentsFinite=True,auxiliaryEosPositions=b['endEosPositions'],auxiliaryEosBatches=b['endEosBatches'],seenTargetTokens=b['seen_tokens'],seenTargetBytes=b['seen_bytes'],noAdditionalOptimizerUpdates=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
  (d/'snapshot.json').write_text(json.dumps(record,indent=2)+'\n');seen.add(n);print(json.dumps(record),flush=True)
 if n==10000:break
 time.sleep(3)
