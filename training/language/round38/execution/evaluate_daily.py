"""Additional everyday-language DEV, not TEST; reuse exact own raw generation."""
import argparse, hashlib, importlib.util, json, pathlib, sys, time
R = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R.parent / 'round10'))
spec = importlib.util.spec_from_file_location('round10_raw_evaluator', R.parent / 'round10/evaluate.py')
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)
p = argparse.ArgumentParser()
p.add_argument('--model', type=pathlib.Path, required=True)
p.add_argument('--out', type=pathlib.Path, required=True)
p.add_argument('--reuse-exact', action='store_true')
a = p.parse_args()
ev.torch.set_num_threads(1)
probes_path = R / 'execution/daily-probes.json'
probes = json.loads(probes_path.read_text())
evaluator_sha = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
raw_evaluator_sha = hashlib.sha256((R.parent / 'round10/evaluate.py').read_bytes()).hexdigest()
if a.reuse_exact and a.out.exists():
    cached = json.loads(a.out.read_text())
    assert cached['modelFileSha256'] == hashlib.sha256(a.model.read_bytes()).hexdigest()
    assert cached['probeSha256'] == hashlib.sha256(probes_path.read_bytes()).hexdigest()
    assert cached['evaluatorSha256'] == evaluator_sha and cached['rawEvaluatorSha256'] == raw_evaluator_sha
    assert cached['evaluationThreads'] == 1 and cached['maxNewTokens'] == 192
    assert len(cached['rows']) == len(probes['probes']) == 12 and len(cached['references']) == 4
    for row, opening in zip(cached['rows'], probes['probes'], strict=True):
        assert all(row[k] == opening[k] for k in ['id', 'group', 'prefix'])
    print(json.dumps(dict(reusedExactSavedGeneration=True, generationSha256=hashlib.sha256(a.out.read_bytes()).hexdigest(), rows=12)), flush=True)
    raise SystemExit(0)
model, export = ev.load_model(a.model)
original = json.loads((R.parent / 'round10/generation-policy.json').read_text())
max_new = original['generation']['maxNewTokens']
assert max_new == 192
report = dict(modelFileSha256=hashlib.sha256(a.model.read_bytes()).hexdigest(), partition='additional-exposed-everyday-development-NOT-TEST', evaluationThreads=1, maxNewTokens=max_new, probeSha256=hashlib.sha256(probes_path.read_bytes()).hexdigest(), usedForWeightSelection=False, evaluatorSha256=evaluator_sha, rawEvaluatorSha256=raw_evaluator_sha, training=export['training'], rows=[], references=[])
for opening in probes['probes']:
    start = time.monotonic()
    result = ev.generate(model, opening['prefix'], export['tokenizer'], max_new)
    report['rows'].append(dict(**opening, **result, elapsedSeconds=time.monotonic()-start))
    print(json.dumps(dict(id=opening['id'], **result), ensure_ascii=False), flush=True)
for row in report['rows'][:4]:
    tokens = [ev.SPECIALS['bos']] + ev.encode_stream(row['prefix'], export['tokenizer'])
    with ev.torch.no_grad():
        logits = model(ev.torch.tensor([tokens]))[0, -1]
    report['references'].append(dict(id=row['id'], tokens=tokens, logits=logits.tolist()))
a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
