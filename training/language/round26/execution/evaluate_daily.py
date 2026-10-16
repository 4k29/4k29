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
a = p.parse_args()
ev.torch.set_num_threads(1)
probes_path = R / 'execution/daily-probes.json'
probes = json.loads(probes_path.read_text())
model, export = ev.load_model(a.model)
original = json.loads((R.parent / 'round10/generation-policy.json').read_text())
max_new = original['generation']['maxNewTokens']
assert max_new == 192
report = dict(modelFileSha256=hashlib.sha256(a.model.read_bytes()).hexdigest(), partition='additional-exposed-everyday-development-NOT-TEST', evaluationThreads=1, maxNewTokens=max_new, probeSha256=hashlib.sha256(probes_path.read_bytes()).hexdigest(), usedForWeightSelection=False, training=export['training'], rows=[], references=[])
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
