"""Only verified own weights; new word rows are scaled means of own glyph rows."""
import hashlib,json,pathlib
import torch
ROOT=pathlib.Path(__file__).resolve().parent;PARENT=ROOT.parent/'round8'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def initialize(model,tokenizer,ancestor=None):
 policy=read(ROOT/'training-policy.json');manifest=PARENT/'reproducibility-manifest.json'
 assert sha(manifest)==policy['parentManifestSha256']
 for entry in read(manifest)['files']:
  path=PARENT/entry['path'];assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],entry['path']
 if ancestor:
  if pathlib.Path(ancestor).name!=ancestor:raise ValueError('Local own ancestor required')
  folder=ROOT/ancestor;result=read(folder/'result.json');saved=torch.load(folder/'checkpoint.pt',map_location='cpu',weights_only=False)
  assert result['completedRun'] and saved['step']==1000 and sorted({int(s['step']) for s in saved['optimizer']['state'].values()})==[1000]
  assert saved['beststep']==result['bestStep'] and saved['config']==model.config and result['ownParentOnly'] and result['ownRandomInitializedLineage']
  assert tokenizer==read(ROOT/f"word-bpe-{result['merges']}/tokenizer.json")
  assert result['trainerSourceSha256']==sha(ROOT/'train.py') and result['initializationSourceSha256']==sha(ROOT/'initialization.py')
  assert result['experimentPolicySha256']==sha(ROOT/'training-policy.json') and result['seed']==policy['seedPilot'] and result['requestedSteps']==policy['pilotSteps']
  model.load_state_dict(saved['beststate']);lineage=result['parentSelectedWeightLineageUpdates']+saved['beststep'];selected=saved['beststep']
 else:
  folder=PARENT/'expanded-characters-10000';result=read(folder/'result.json');saved=torch.load(folder/'checkpoint.pt',map_location='cpu',weights_only=False)
  assert result['completedRun'] and saved['step']==saved['beststep']==10000 and sorted({int(s['step']) for s in saved['optimizer']['state'].values()})==[10000]
  assert result['ownParentOnly'] and result['ownRandomInitializedLineage'] and saved['config']['layers']==model.config['layers']==8
  assert all(v==model.config[k] for k,v in saved['config'].items() if k!='vocabulary')
  previous=read(PARENT/'unicode-bpe-4578/tokenizer.json');assert tokenizer['bytes'][:len(previous['bytes'])]==previous['bytes'] and tokenizer['merges'][:len(previous['merges'])]==previous['merges']
  base_meta=read(ROOT/'preparation.json');base=read(ROOT/f"unicode-bpe-{base_meta['merges']}/tokenizer.json");assert tokenizer['bytes'][:len(base['bytes'])]==base['bytes']
  glyphs={r['character']:r['token'] for r in read(ROOT/'character-frequencies.json')};state=model.state_dict()
  with torch.no_grad():
   state['token.weight'].zero_();state['token.weight'][:len(previous['bytes'])].copy_(saved['beststate']['token.weight'])
   for k,v in saved['beststate'].items():
    if k!='token.weight':state[k].copy_(v)
   for token in range(len(base['bytes']),len(tokenizer['bytes'])):
    chars=bytes.fromhex(tokenizer['bytes'][token]).decode('utf-8');state['token.weight'][token].copy_(.95*state['token.weight'][[glyphs[c] for c in chars]].mean(0))
  lineage=result['parentSelectedWeightLineageUpdates']+saved['beststep'];selected=saved['beststep']
 assert not any(result[k] for k in ['externalWeights','externalTokenizer','externalInferenceAPI'])
 assert result['checkpointSha256']==sha(folder/'checkpoint.pt')
 return dict(parentCheckpointSha256=sha(folder/'checkpoint.pt'),parentCompletedSteps=saved['step'],parentSelectedSteps=selected,parentSelectedWeightLineageUpdates=lineage,ownParentOnly=True,ownRandomInitializedLineage=True,randomInitialization=False,optimizerReset=True,seedReset=True,wordRowsInitialization='0.95 times own TRAIN glyph-vector means; no external embeddings',ownAncestor=ancestor)
