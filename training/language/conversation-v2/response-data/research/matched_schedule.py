"""Data-only nonrepeating source comparison; never constructs model/optimizer.

Candidate feasibility is separate from training permission. Exactly one selected
complete path per source family avoids multiplying its shared prefix. Ordinary
full CE means all prefix text must be safe, not just the final response.
"""
import argparse
import array
import collections
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parents[1]


def rank(scope, ident):
    return hashlib.sha256(('response-match-v1|' + scope + '|' + str(ident)).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dose(seq):
    targets = seq[1:]
    return {'targets': len(targets), 'body': sum(t >= 6 for t in targets),
            'eos': targets.count(2), 'roles': sum(t in (3,4) for t in targets),
            'bos': targets.count(1)}


def match(native, rp, cap=2048):
    """Return unique native/RP replacements and separate unused shared RP.

    Short tails remain eligible. No target padding, cutting or synthetic EOS.
    Caller must supply streams with genuine original boundaries.
    """
    if not 1 <= cap <= 2048:
        raise ValueError('Invalid preregistered cap')
    buckets = collections.defaultdict(list)
    for i, row in enumerate(rp):
        if not 2 <= len(row) <= 257:
            raise ValueError('Invalid RP window')
        buckets[len(row)-1].append(i)
    for bucket in buckets.values():
        bucket.sort(key=lambda i: rank('rp-replace', i), reverse=True)
    matched = []
    skipped = collections.Counter()
    for row in sorted(native, key=lambda d: rank('native-window', d['id'])):
        seq = row['tokens']
        if not 2 <= len(seq) <= 257:
            raise ValueError('Invalid native window')
        n = len(seq)-1
        if not buckets[n]:
            skipped[n] += 1
            continue
        matched.append((row, buckets[n].pop()))
        if len(matched) == 2*cap:
            break
    if len(matched) % 2:
        matched.pop()
    used = {index for _, index in matched}
    common = sorted((i for i in range(len(rp)) if i not in used),
                    key=lambda i: rank('rp-shared', i))[:len(matched)]
    if len(common) != len(matched):
        raise ValueError('Insufficient distinct shared RP windows')
    return matched, common, dict(skipped)


def build(candidates, output, decisions=None):
    output.mkdir(parents=True, exist_ok=False)
    data_path = V2/'data/data.json'
    meta = json.loads(data_path.read_text())
    repo = V2.parents[2]
    token_path = repo/meta['trainTokensPath']
    if sha(token_path) != meta['trainTokensSha256']:
        raise ValueError('RP token checksum mismatch')
    values = array.array('I')
    values.frombytes(token_path.read_bytes())
    if values.itemsize != 4:
        raise ValueError('Expected uint32')
    rp = [values[w['offset']:w['offset']+w['length']].tolist() for w in meta['trainWindows']]
    approved = None
    if decisions:
        result = json.loads(decisions.read_text())
        result = result['decisions'] if isinstance(result, dict) else result
        approved = {d['id'] for d in result if d.get('decision') == 'accept'
                    and d.get('full_history_safe_for_ce') is True}
    by_family = {}
    rows = [json.loads(line) for line in gzip.open(candidates, 'rt')]
    for row in rows:
        if row['partition'] not in ('TRAIN', 'TRAIN-candidate'):
            raise ValueError('Non-TRAIN row in source feasibility pool')
        if approved is not None and row['id'] not in approved:
            continue
        seq = row['serialized_ids']
        if not seq or seq[0] != 1 or seq[-1] != 2 or 0 in seq:
            raise ValueError('Malformed real source stream')
        family = row['family']
        old = by_family.get(family)
        if old is None or rank('one-path-family', row['id']) < rank('one-path-family', old['id']):
            by_family[family] = row
    native = []
    for family, row in sorted(by_family.items()):
        seq = row['serialized_ids']
        for offset in range(0, len(seq)-1, 256):
            tokens = seq[offset:offset+257]
            native.append({'id': row['id']+'@'+str(offset), 'source_response_id': row['id'],
                           'family': family, 'offset': offset,
                           'true_path_end': offset+len(tokens) == len(seq), 'tokens': tokens})
    matched, common, skipped = match(native, rp)
    doses = {'control': collections.Counter(), 'treatment': collections.Counter(),
             'native': collections.Counter()}
    schedule = []
    for step in range(len(matched)//2):
        chosen = matched[step*2:step*2+2]
        shared = common[step*2:step*2+2]
        control = [rp[i] for i in shared] + [rp[index] for _, index in chosen]
        treatment = [rp[i] for i in shared] + [row['tokens'] for row, _ in chosen]
        if [len(s) for s in control] != [len(s) for s in treatment]:
            raise ValueError('Per-slot active target mismatch')
        for arm, seqs in [('control',control), ('treatment',treatment),
                          ('native',[row['tokens'] for row,_ in chosen])]:
            for seq in seqs:
                doses[arm].update(dose(seq))
        schedule.append({'step': step+1, 'shared_rp_indices': shared,
                         'control_replacement_rp_indices': [i for _,i in chosen],
                         'native_windows': [row for row,_ in chosen],
                         'active_targets_both': sum(len(s)-1 for s in control)})
    with (output/'schedule.jsonl.gz').open('wb') as file:
        with gzip.GzipFile(fileobj=file, mode='wb', mtime=0) as compressed:
            for row in schedule:
                compressed.write((json.dumps(row, ensure_ascii=False, separators=(',', ':'))+'\n').encode())
    result = {'status': 'candidate-feasibility-only' if decisions is None else 'quality-filtered-feasibility-only',
              'training_authorized': False, 'optimizer_updates': 0, 'model_objects': 0,
              'candidate_input_sha256': sha(candidates),
              'decisions_sha256': sha(decisions) if decisions else None,
              'selected_source_families': len(by_family), 'native_pool_windows': len(native),
              'selected_native_windows': len(matched), 'steps_per_arm': len(schedule),
              'padded_batch_shape': [4,256], 'doses': {k: dict(v) for k,v in doses.items()},
              'native_genuine_path_ends': sum(r['true_path_end'] for r,_ in matched),
              'native_length_without_rp_match': skipped,
              'distinct_rp_windows_total': len(matched)+len(common),
              'schedule_sha256': sha(output/'schedule.jsonl.gz'),
              'no_source_window_repetition': True,
              'source_family_policy': 'one complete SHA-first candidate path per family; no branch-prefix multiplication',
              'limitations': ['Not formally admitted TRAIN', 'No state-changing resume test executed',
                              'Exact slot target counts match; body/EOS/role doses differ as measured',
                              'Smaller actual source budget is not evidence of sufficient language training']}
    (output/'receipt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidates', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--decisions', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.candidates, args.output, args.decisions), ensure_ascii=False, indent=2))
