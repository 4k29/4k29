"""Prepare unmodified exposed-DEV outputs for future human review; no ratings."""
import argparse
import gzip
import hashlib
import json
import pathlib
import secrets

D = pathlib.Path(__file__).resolve().parent
N = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', nargs='+', required=True)
    args = parser.parse_args()
    out = D/'blind-review'
    assert not out.exists(), 'Keep prior review materials unchanged'
    salt_path = N/'private/blind-review-salt.txt'
    if not salt_path.exists():
        salt_path.write_text(secrets.token_hex(32))
    salt = salt_path.read_text().strip()
    pieces = [bytes.fromhex(t) for t in json.loads((N.parent/'data/tokenizer.json').read_text())['bytes']]
    rows, keys, inputs = [], {}, {}
    for model in args.models:
        paths = [D/'evaluation'/f'{model}.json', D/'panels'/f'{model}.json']
        for path in paths:
            if not path.exists():
                assert model.endswith('-0') and path.parent.name == 'panels'
                continue
            inputs[str(path.relative_to(N))] = sha(path)
            obj = json.loads(path.read_text())
            groups = {'prose': obj['cases']} if 'cases' in obj else {
                'legacy': obj['legacy'], 'grounded': obj['grounded36'], 'context': obj['context12']}
            for group, cases in groups.items():
                for index, case in enumerate(cases):
                    if case.get('panel') in ['train4', 'train-caption4']:
                        continue
                    # All cases are existing exposed DEV. No TEST or hidden reference is opened.
                    identity = f'{model}|{group}|{index}'
                    key = hashlib.sha256((salt+'|'+identity).encode()).hexdigest()[:24]
                    prefix_bytes = b''.join(pieces[t] for t in case['prefix'])
                    prompt = prefix_bytes.decode('utf8')
                    rows.append(dict(review_id=key, kind=case.get('panel', group),
                                     prompt=case.get('prompt', prompt), prefix_text=prompt,
                                     generated_text=case['text'],
                                     generated_raw_bytes_hex=case['rawBytesHex'],
                                     generated_token_ids=case['tokensIncludingEos'],
                                     stop_reason=case['stopReason'],
                                     required_content=case.get('requirement'),
                                     human_rating=None))
                    keys[key] = dict(model=model, group=group, source=str(path.relative_to(N)),
                                     index=index, case_id=case.get('id'))
    rows.sort(key=lambda row: hashlib.sha256((salt+'|order|'+row['review_id']).encode()).hexdigest())
    out.mkdir()
    path = out/'materials.jsonl.gz'
    with path.open('wb') as handle:
        with gzip.GzipFile(fileobj=handle, mode='wb', filename='', mtime=0) as zipped:
            for row in rows:
                zipped.write((json.dumps(row, ensure_ascii=False)+'\n').encode())
    (N/'private/blind-review-key.json').write_text(json.dumps(keys, indent=2)+'\n')
    manifest = dict(materials_sha256=sha(path), cases=len(rows), input_sha256=inputs,
                    private_salt_sha256=sha(salt_path), human_ratings_received=0,
                    independent_native_evaluation_completed=False,
                    scope='Future blinded review materials only. Existing exposed exploratory DEV; '
                          'not a new independent TEST. No reference/image matching for captions. '
                          'Judge Japanese, contextual appropriateness, full-output coherence, '
                          'repetition and meaningful ending separately. No rubric/gate relaxation. '
                          'Model key remains private until ratings are fixed. Main agent is already unblinded.')
    (out/'MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(manifest)


if __name__ == '__main__':
    main()
