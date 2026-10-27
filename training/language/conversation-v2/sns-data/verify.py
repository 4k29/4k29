"""Offline verification; never downloads data, opens weights or calls an optimizer."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def artifacts():
    return [p for p in sorted(HERE.rglob('*')) if p.is_file()
            and '__pycache__' not in p.parts
            and p.name not in ('MANIFEST.json', 'verification.log')]


def run(freeze=False):
    manifest = HERE / 'MANIFEST.json'
    if freeze:
        manifest.write_text(json.dumps({
            'purpose': 'data-only study; no optimizer updates or formal model training',
            'actual_optimizer_updates': 0,
            'artifacts': [{'path': str(p.relative_to(HERE)), 'bytes': p.stat().st_size,
                           'sha256': sha(p)} for p in artifacts()]},
            ensure_ascii=False, indent=2) + '\n')
    data = json.loads(manifest.read_text())
    assert data['actual_optimizer_updates'] == 0
    expected = set()
    for row in data['artifacts']:
        p = HERE / row['path']
        assert p.resolve().is_relative_to(HERE)
        assert p.stat().st_size == row['bytes'], row['path']
        assert sha(p) == row['sha256'], row['path']
        expected.add(p)
    assert set(artifacts()) == expected, 'Missing or unmanifested artifact'
    raw = HERE / 'raw/mrmpc-dialogues.jsonl.gz'
    if raw.exists():
        receipt = json.loads((HERE / 'raw/acquisition.json').read_text())
        assert sha(raw) == receipt['archiveSha256']
        rows = [json.loads(line) for line in gzip.open(raw, 'rt')]
        assert len(rows) == receipt['dialogues'] == 960
        assert len({r['path'] for r in rows}) == len(rows)
        assert sum(len(r['data']['utterances']) if 'data' in r else r['source_utterances']
                   for r in rows) == 100680
        assert all('data' not in r for r in rows if r.get('withheld'))
    for metrics, corpus in [('metrics.json', 'conversations.jsonl.gz'),
                            ('oasst-metrics.json', 'oasst-conversations.jsonl.gz')]:
        m = json.loads((HERE/'derived'/metrics).read_text())
        assert sha(HERE/'derived'/corpus) == m['derived_sha256']
        assert m['actual_optimizer_updates'] == m['training_admitted_dialogues'] == 0
        assert m['sealed_test_created_or_read'] is False
    print(json.dumps({'passed': True, 'verified_artifacts': len(expected),
                      'optimizer_updates': 0, 'network_requests': 0,
                      'model_weights_opened': 0}, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--freeze', action='store_true', help='Record artifacts after all audits finish')
    run(p.parse_args().freeze)
