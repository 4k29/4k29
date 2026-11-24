"""Post-training paired exposure and unchanged-prefix audit; no model forwards/updates."""
import pathlib,sys,json,hashlib,torch
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round42';sys.path.insert(0,str(R));from prefix_selection import load_selector
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();torch.set_num_threads(1)
a=torch.load(P/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);b=torch.load(R/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
assert a['step']==b['step']==10000
za=torch.load(P/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False);zb=torch.load(R/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False)
assert za['pythonRng']==zb['pythonRng']and torch.equal(za['torchRng'],zb['torchRng'])
assert za['config']==zb['config']and all(torch.equal(v,zb['model'][k])for k,v in za['model'].items())
assert za['optimizer']['param_groups']==zb['optimizer']['param_groups']
for k,state in za['optimizer']['state'].items():
 for n,t in state.items():assert torch.equal(t,zb['optimizer']['state'][k][n])
assert a['settings']['genreSampling']==b['settings']['genreSampling'] and a['config']==b['config']
for n in ['batching.py','objective.py','sequence_objective.py','rollout_trace.py','initialization.py','prefix_selection.py','utterance_end_objective.py','end_main_ce.py']:assert sha(P/n)==sha(R/n),n
for n in ['multiview/validation.index.json','multiview/validation.tokens.bin','multiview/tokenizer.json']:assert sha(P/n)==sha(R/n),n
assert sha(P/'context_preference.py')==sha(R/'context_preference.py') and sha(P/'train.py')==sha(R/'train.py')
for n in ['train.index.json','train.tokens.bin']:assert sha(P/'multiview'/n)==sha(R/'multiview'/n)
assert a['history'][0]['validation']==b['history'][0]['validation']
assert read(R/'execution/data-preflight.json')['allOldTokenBytesExactlyPreserved']
assert read(R/'execution/sampler-replay.json')['endingPythonRngExactlyMatches']
assert a['pythonRng']==b['pythonRng'] and torch.equal(a['torchRng'],b['torchRng'])
assert a['seen_tokens']==b['seen_tokens'] and a['seen_bytes']==b['seen_bytes']
report=dict(actualUpdatesEach=10000,pairedComparator='round42',sameAlignedInitialModelOptimizerAndRng=True,allOtherCoreLearningCodeByteIdentical=True,oldDataPrefixAndValidationUnchanged=True,oneChangedFactor='Auxiliary pool size256 to1024 only',positiveDrawsAndFinalRngExpectedToMatch=True,ownSamplerReplayExactlyMatchesOwnCheckpoint=True,sameFinalPythonRng=a['pythonRng']==b['pythonRng'],sameFinalTorchRng=torch.equal(a['torchRng'],b['torchRng']),additionalOptimizerUpdates=0,controlCheckpointSha256=sha(P/'continue-10000/checkpoint.pt'),childCheckpointSha256=sha(R/'continue-10000/checkpoint.pt'))
(R/'execution/paired-training-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
