"""Post-selection TRAIN-only gradient/saturation probe; no updates or condition tuning."""
import pathlib,sys,json,math
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));import train as t
from sequence_objective import rollout_unlikelihood,repeated_generated_positions
t.torch.set_num_threads(1);fixed_source=R.parent/f'round{25}'/'execution/sequence-gradient-diagnostic.json';fixed=t.read(fixed_source)['batches'];initial=t.torch.load(R.parent/'round11/continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);vocab=[bytes.fromhex(x) for x in t.read(R/'multiview/tokenizer.json')['bytes']];models={}
for name,root in [('old',R.parent/'round25'),('new',R)]:
 cp=t.torch.load(root/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);assert cp['step']==10000
 model=t.Decoder(cp['config']);model.load_state_dict(cp['beststate']);model.train();t.torch.set_rng_state(initial['torchRng']);rows=[]
 for batch in fixed:
  prefix=t.torch.tensor([batch['tokens'][:batch['prefixLength']]]);loss,record=rollout_unlikelihood(model,prefix);grads=t.torch.autograd.grad(loss,list(model.parameters()));norm=math.sqrt(sum(float(g.double().square().sum()) for g in grads));tokens=record['tokens'];repeated,_=repeated_generated_positions(tokens,record['prefixLength'])
  with t.torch.random.fork_rng(devices=[]):
   # Same dropout state as rollout_unlikelihood's differentiable forward.
   with t.torch.no_grad():scores=model(tokens[:,:-1]);p=t.F.log_softmax(scores,-1).gather(-1,tokens[:,1:].unsqueeze(-1)).squeeze(-1).exp()
  selected=p[repeated];raw=b''.join(vocab[i] for i in tokens[0,record['prefixLength']:].tolist())
  try:text=raw.decode('utf8')
  except UnicodeDecodeError:text=None
  rows.append(dict(batch=batch['batch'],sourceRow=batch['sourceRow'],tokens=tokens[0].tolist(),prefixLength=record['prefixLength'],generatedTokens=record['generatedTokens'],negativePositions=record['negativePositions'],sequenceLoss=float(loss.detach()),sequenceGradientNorm=norm,allGradientsFinite=all(bool(t.torch.isfinite(g).all()) for g in grads),cappedNegativePositions=int((selected>1-1e-6).sum()),negativeProbabilityMin=float(selected.min()) if len(selected) else None,negativeProbabilityMax=float(selected.max()) if len(selected) else None,generatedRawUtf8Hex=raw.hex(),generatedText=text))
 assert all(t.torch.equal(v,model.state_dict()[k]) for k,v in cp['beststate'].items())
 assert all(x['allGradientsFinite'] for x in rows)
 models[name]=dict(checkpointSha256=t.sha(root/'continue-10000/checkpoint.pt'),selectedStep=cp['beststep'],rows=rows,negativePositions=sum(x['negativePositions'] for x in rows),cappedNegativePositions=sum(x['cappedNegativePositions'] for x in rows),activeRollouts=sum(x['negativePositions']>0 for x in rows),activeRolloutsWithZeroGradient=sum(x['negativePositions']>0 and x['sequenceGradientNorm']==0 for x in rows))
t.write(R/'execution/sequence-saturation.json',dict(models=models,postSelectionDiagnostic=True,usedForSelection=False,conditionsChanged=False,trainOnly=True,independentLanguageEvaluation=False,noDevelopmentOrTestRead=True,additionalOptimizerUpdates=0,optimizerInstantiated=False,weightsUnchanged=True,dropoutMode='train, forked initial own-parent Torch RNG',fixedPrefixesReference=str(fixed_source.relative_to(R.parent)),fixedPrefixesSha256=t.sha(fixed_source),scope='16 identical true TRAIN prefixes at selected raw FP32 weights, deterministic greedy64 and original sequence loss. Repeated-target cap/gradient diagnosis; not a language score or estimate over all training histories.'))
print(json.dumps({k:{q:v[q] for q in ['selectedStep','negativePositions','cappedNegativePositions','activeRollouts','activeRolloutsWithZeroGradient']} for k,v in models.items()}))
