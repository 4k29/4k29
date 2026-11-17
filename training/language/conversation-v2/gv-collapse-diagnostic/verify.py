"""Verify recorded replay and corpus evidence without loading checkpoints."""
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path

root = Path(__file__).resolve().parent
plan = root / 'PLAN.json'
assert sha256(plan.read_bytes()).hexdigest() == (root / 'PLAN.sha256').read_text().strip()
with gzip.open(root / 'DIAGNOSTIC.json.gz', 'rt') as stream:
    result = json.load(stream)
rows = result['cases']
assert result['optimizer_calls'] == 0
assert Counter(r['model'] for r in rows) == {'initial': 18, 'B-terminal': 18, 'C-terminal': 18}
assert result['forwards'] == 2 * len(rows) + sum(len(r['exact_history_probes']) for r in rows)
for row in rows:
    assert [x['argmax'] for x in row['paths']['self']] == row['generated']
    assert row['maximum_history'] < 256
    if row['repeat']:
        assert row['exact_history_probes']
    for probe in row['exact_history_probes'].values():
        assert probe['argmax'] == probe['archived']
        assert probe['max_top10_probability_difference'] < 1e-5
with gzip.open(root / 'ADDITIONAL.jsonl.gz', 'rt') as stream:
    corpus = [json.loads(line) for line in stream]
assert len({r['family'] for r in corpus}) == len(corpus) == 4
assert sum(len(r['tokens']) - 1 for r in corpus) == 599
assert all(2 not in r['tokens'] for r in corpus)
print('PASS: frozen plan, replay, exact-history probes, data counts and zero updates')
