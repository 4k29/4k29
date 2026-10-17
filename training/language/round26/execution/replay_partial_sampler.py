"""Read-only sampler replay from initial RNG to an actual saved partial checkpoint."""
import collections, datetime, hashlib, io, json, pathlib, random, sys
R = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R))
from train import torch, np, load_partition, sampler, draw, read

torch.set_num_threads(1)
# Bind the evidence to exactly the bytes loaded, even while the trainer replaces its file.
raw = (R / 'continue-10000/checkpoint.pt').read_bytes()
cp = torch.load(io.BytesIO(raw), map_location='cpu', weights_only=False)
zero = torch.load(R / 'continue-10000/checkpoint-0.pt', map_location='cpu', weights_only=False)
assert 0 <= cp['step'] <= 10000
assert cp['settings'] == zero['settings']
rng = random.Random()
rng.setstate(zero['pythonRng'])
info, values = load_partition(R / 'multiview', 'train')
strata, weights, masses = sampler(info['rows'], cp['settings']['genreSampling'])
tok = read(R / 'multiview/tokenizer.json')
byte_lengths = np.array([len(bytes.fromhex(b)) for b in tok['bytes']], dtype=np.int64)
counts = collections.Counter()
tokens = utf8_bytes = 0
for step in range(1, cp['step'] + 1):
    width, rows = draw(rng, cp['settings']['batch'], strata, weights, masses)
    for row in rows:
        target = values[row['offset'] + row['prefixLength']:row['offset'] + row['length']]
        tokens += len(target)
        utf8_bytes += int(byte_lengths[target].sum())
        counts[row['site']] += 1
assert rng.getstate() == cp['pythonRng'], 'Private sampler RNG differs from uninterrupted draws'
assert tokens == cp['seen_tokens'] and utf8_bytes == cp['seen_bytes']
assert sum(counts.values()) == cp['step'] * cp['settings']['batch']
record = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), actualSavedUpdates=cp['step'], checkpointSha256=hashlib.sha256(raw).hexdigest(), endingPythonRngExactlyMatchesUninterrupted=True, targetTokens=tokens, targetUtf8Bytes=utf8_bytes, exposureCountsExactlyMatch=True, rowsBySite=dict(counts), additionalOptimizerUpdates=0, forwardOrBackwardExecuted=False, trainingConditionsChanged=False, newTestUsed=False)
out = R / 'execution' / f"partial-sampler-replay-{cp['step']}.json"
out.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record), flush=True)
