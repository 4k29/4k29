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
site_tokens=collections.Counter();site_bytes=collections.Counter();human_views=collections.Counter();human_docs=set()
tokens = utf8_bytes = 0
for step in range(1, cp['step'] + 1):
    width, rows = draw(rng, cp['settings']['batch'], strata, weights, masses)
    for row in rows:
        target = values[row['offset'] + row['prefixLength']:row['offset'] + row['length']]
        tokens += len(target)
        utf8_bytes += int(byte_lengths[target].sum())
        counts[row['site']] += 1
        site_tokens[row['site']]+=len(target);site_bytes[row['site']]+=int(byte_lengths[target].sum())
        if row['site']=='human-chat':human_views[row['variant']]+=int(byte_lengths[target].sum());human_docs.add(row['document'])
assert rng.getstate() == cp['pythonRng'], 'Private sampler RNG differs from uninterrupted draws'
assert tokens == cp['seen_tokens'] and utf8_bytes == cp['seen_bytes']
assert sum(counts.values()) == cp['step'] * cp['settings']['batch']
record = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), actualSavedUpdates=cp['step'], checkpointSha256=hashlib.sha256(raw).hexdigest(), endingPythonRngExactlyMatchesUninterrupted=True, targetTokens=tokens, targetUtf8Bytes=utf8_bytes, exposureCountsExactlyMatch=True, rowsBySite=dict(counts), additionalOptimizerUpdates=0, forwardOrBackwardExecuted=False, trainingConditionsChanged=False, newTestUsed=False)
population={d['sourceDocument'] for d in info['documents'] if d['site']=='human-chat'}
raw_human_bytes=sum(d['utf8Bytes'] for d in info['documents'] if d['site']=='human-chat' and d['variant']==0)
assert sum(site_tokens.values())==tokens and sum(site_bytes.values())==utf8_bytes and len(population)==8975
record.update(targetTokensBySite=dict(site_tokens),targetBytesBySite=dict(site_bytes),humanTargetBytesByView=dict(human_views),humanTrainSourcePopulation=len(population),humanUniqueSourceDocumentsSelected=len(human_docs),humanOriginalCorpusBytes=raw_human_bytes,humanTargetByteEquivalentPassesAcrossMixedViews=site_bytes['human-chat']/raw_human_bytes,coverageLimitation='Byte-equivalent exposure includes repeated windows across token views; not unique raw-byte coverage, full-dialogue coverage, semantic understanding, or proof of insufficient training.')
out = R / 'execution' / f"partial-domain-exposure-{cp['step']}.json"
out.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record), flush=True)
