"""Fail-closed source/consent gate and source-scoped withdrawal lineage.

No networking, training, identity linking, or claims of model unlearning.
Inputs contain local pseudonyms, not emails or account credentials.
"""
import hashlib
import json
from pathlib import Path

REQUIRED = ('acquisition', 'storage', 'training', 'redistribution')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def rights_gate(source, now):
    """ISO date comparison, no inferred grants from public API availability."""
    reasons = []
    if not source.get('evidence'):
        reasons.append('missing-primary-evidence')
    if not source.get('reviewed_on') or source['reviewed_on'] > now:
        reasons.append('missing-or-future-review-date')
    if not source.get('recheck_by') or source['recheck_by'] < now:
        reasons.append('rights-review-expired')
    for right in REQUIRED:
        if source.get('permissions', {}).get(right) != 'allowed':
            reasons.append(right + '-not-confirmed')
    if not source.get('attribution') or not source.get('license'):
        reasons.append('missing-license-or-attribution')
    return {'rights_qualified': not reasons, 'reasons': reasons,
            'final_training_admitted': False,
            'remaining_checks': ['record-rights-exceptions', 'privacy', 'quality',
                                 'split-and-evaluation-overlap', 'resource-and-protocol']}


def withdrawal_plan(records, requests, artifacts):
    """Exclude whole affected conversations; all downstream artifacts need rebuild.

    records: {source,id,speakers:[source-local pseudonyms]}.
    requests: {source,kind:conversation|speaker,id}; no cross-source matching.
    artifacts: {id,record_ids:[source-qualified 'source/id'],parents:[artifact id]}.
    Does not physically delete files/history or alter any checkpoint.
    """
    removed = set()
    for q in requests:
        if q.get('kind') not in ('conversation', 'speaker'):
            raise ValueError('Unsupported withdrawal selector')
        for r in records:
            if r['source'] != q['source']:
                continue
            matched = r['id'] == q['id'] if q['kind'] == 'conversation' else q['id'] in r['speakers']
            if matched:
                removed.add(r['source'] + '/' + r['id'])
    ids = [a['id'] for a in artifacts]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate artifact IDs')
    known = set(ids)
    if any(set(a.get('parents', [])) - known for a in artifacts):
        raise ValueError('Unknown parent artifact')
    invalid = set()
    while True:
        before = len(invalid)
        for a in artifacts:
            if removed.intersection(a.get('record_ids', [])) or invalid.intersection(a.get('parents', [])):
                invalid.add(a['id'])
        if len(invalid) == before:
            break
    return {'excluded_records': sorted(removed), 'invalidate_artifacts': sorted(invalid),
            'request_digest': digest(requests), 'performed_deletions': 0,
            'model_unlearning_performed': False,
            'action': 'quarantine; rebuild all affected descendants; review trained weights separately'}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    data = json.loads(args.input.read_text())
    result = withdrawal_plan(data['records'], data['requests'], data['artifacts'])
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
