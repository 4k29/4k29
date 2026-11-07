"""Post-training paired exposure and prefix-only audit; no model forwards/updates."""
import pathlib,sys,json,hashlib,torch
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round33';sys.path.insert(0,str(R));from prefix_selection import load_selector
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();torch.set_num_threads(1)
a=torch.load(P/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);b=torch.load(R/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
assert a['step']==b['step']==10000
za=torch.load(P/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False);zb=torch.load(R/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False)
assert za['pythonRng']==zb['pythonRng']and torch.equal(za['torchRng'],zb['torchRng'])
assert za['config']==zb['config']and all(torch.equal(v,zb['model'][k])for k,v in za['model'].items())
assert za['optimizer']['param_groups']==zb['optimizer']['param_groups']
for k,state in za['optimizer']['state'].items():
 for n,t in state.items():assert torch.equal(t,zb['optimizer']['state'][k][n])
assert a['pythonRng']==b['pythonRng']and torch.equal(a['torchRng'],b['torchRng'])
assert a['seen_tokens']==b['seen_tokens']and a['seen_bytes']==b['seen_bytes']
assert a['settings']['genreSampling']==b['settings']['genreSampling']and a['config']==b['config']
for n in ['batching.py','objective.py','sequence_objective.py','rollout_trace.py','initialization.py']:assert sha(P/n)==sha(R/n),n
for n in ['multiview/train.index.json','multiview/train.tokens.bin','multiview/validation.index.json','multiview/validation.tokens.bin','multiview/tokenizer.json','sources/documents.jsonl']:assert sha(P/n)==sha(R/n),n
for x,y in zip(a['history'],b['history'],strict=True):
 assert x['step']==y['step']and x.get('seenTargetTokens',0)==y.get('seenTargetTokens',0)and x.get('seenTargetUtf8Bytes',0)==y.get('seenTargetUtf8Bytes',0)
assert a['history'][0]['validation']==b['history'][0]['validation']
assert read(P/'execution/sampler-replay.json')['drawTraceSha256']==read(R/'execution/sampler-replay.json')['drawTraceSha256']
selector=load_selector(R/'human-turn-token-boundaries.json',read(R/'multiview/tokenizer.json'),read(R/'multiview/train.index.json'),read(R/'policy.json')['humanNegativePrefix']['featureMapSha256'],sha(R/'multiview/tokenizer.json'),sha(R/'multiview/train.index.json'),sha(R/'sources/documents.jsonl'))
old=[json.loads(s)for s in (P/'continue-10000/training-rollouts.jsonl').read_text().splitlines()];new=[json.loads(s)for s in (R/'continue-10000/training-rollouts.jsonl').read_text().splitlines()];assert len(old)==len(new)==1000;changed=human=0
for x,y in zip(old,new,strict=True):
 assert x['step']==y['step']and x['sourceRow']==y['sourceRow'];row=x['sourceRow'];base=min(32,row['length']-1);assert x['prefixLength']==base
 n=selector.length(row,x['tokens'][0]);assert y['prefixLength']==n and y['tokens'][:n]==x['tokens'][:n]
 human+=row['site']=='human-chat';changed+=n!=base
 if row['site']!='human-chat':assert n==base
report=dict(actualUpdatesEach=10000,pairedComparator='round33',sameAlignedInitialModelOptimizerAndRng=True,sameFinalTorchAndPythonRng=True,samePositiveSamplerDrawTraceAndAllTargetCounts=True,unchangedDataTokenizerObjectiveAndInitialization=True,negativeCallsEach=1000,matchedHumanNegativeCalls=human,changedHumanNegativePrefixes=changed,onlyHumanPrefixEndPolicyChanged=True,shorterPrefixLengthPartOfTreatment=True,notPureBoundaryMechanismProof=True,noModelForwardOrOptimizer=True,additionalOptimizerUpdates=0,parentCheckpointSha256=sha(P/'continue-10000/checkpoint.pt'),childCheckpointSha256=sha(R/'continue-10000/checkpoint.pt'),codeSha256=sha(pathlib.Path(__file__)))
(R/'execution/paired-training-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
