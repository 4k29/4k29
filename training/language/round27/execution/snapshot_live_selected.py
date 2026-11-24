"""Read-only selected inference snapshot while training continues; never resume from it."""
import hashlib, io, json, pathlib, sys
R = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R))
import train as t
t.torch.set_num_threads(1)
raw = (R / 'continue-10000/checkpoint.pt').read_bytes()
cp = t.torch.load(io.BytesIO(raw), map_location='cpu', weights_only=False)
assert 0 < cp['step'] < 10000
assert cp['bestloss'] == min(x['validation']['nllPerUtf8Byte'] for x in cp['history'])
out = R / 'execution' / f"interim-daily-{cp['step']}"
out.mkdir(exist_ok=False)
source_sha = hashlib.sha256(raw).hexdigest()
training = dict(**cp['settings'], completedRun=False, completedSteps=cp['step'], requestedSteps=10000, bestStep=cp['beststep'], parameters=sum(t.numel() for t in cp['beststate'].values()), interimInferenceDiagnostic=True, sourceLatestCheckpointSha256=source_sha, history=cp['history'])
tok = t.read(R / 'multiview/tokenizer.json')
t.torch.save(dict(config=cp['config'], state=cp['beststate'], selectedStep=cp['beststep'], actualRetainedUpdates=cp['step'], inferenceOnlyNotResumable=True, sourceLatestCheckpointSha256=source_sha), out / 'selected-inference-weights.pt')
t.export_model(None, cp['beststate'], tok, cp['config'], training, out / 'model.js')
record = dict(actualRetainedUpdatesAtSnapshot=cp['step'], selectedStep=cp['beststep'], bestDevelopmentNll=cp['bestloss'], sourceLatestCheckpointSha256=source_sha, inferenceOnlyNotResumable=True, noOptimizerOrRngInThisInferenceSnapshot=True, latestResumeCheckpoint='continue-10000/checkpoint.pt', additionalOptimizerUpdates=0, conditionsChanged=False, selectedUsingGeneratedOutputs=False, files={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['selected-inference-weights.pt', 'model.js']})
(out / 'snapshot.json').write_text(json.dumps(record, indent=2)+'\n')
print(str(out), flush=True)
