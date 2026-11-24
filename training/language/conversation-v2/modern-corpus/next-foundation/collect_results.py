"""Aggregate finished one-pass results and actual calls; no inferred semantic scores."""
import csv
import hashlib
import json
import pathlib
import re

D = pathlib.Path(__file__).resolve().parent
RUN = D.parent/'private/next-run'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = read(D/'PLAN.json')
    selection = read(D/'SERIES_SELECTION.json')
    selected = selection['selected_arm']
    required = [f'{a}-{plan["comparison_updates"]}' for a in ['A', 'B']]
    required += [f'{selected}-{plan[key]}' for key in ['midpoint_updates', 'full_pass_updates']]
    for name in required:
        for folder in ['evaluation', 'panels', 'context']:
            assert (D/folder/f'{name}.json').exists(), (folder, name)
        review = read(D/'evaluation'/f'{name}-READING.json')
        assert isinstance(review['content_panels'], dict), 'Full reading still pending'
    calls, arms = [], {}
    for arm in ['A', 'B']:
        end = plan['full_pass_updates'] if arm == selected else plan['comparison_updates']
        receipt = read(RUN/arm/f'receipt-{end:05d}.json')
        events = [json.loads(line) for line in (RUN/arm/'updates.jsonl').read_text().splitlines()]
        assert [(e['phase'], e['step']) for e in events if e['event'] == 'intent'] == [
            (e['phase'], e['step']) for e in events if e['event'] == 'completed']
        done = [e for e in events if e['event'] == 'completed']
        assert len(done) == receipt['actual_optimizer_calls']
        arms[arm] = dict(receipt=receipt,
                         all_physical_processed_targets=sum(e['trace']['targets'] for e in done),
                         actual_completed_calls=len(done),
                         validation_calls=sum(e['phase'] == 'resume-validation' for e in done),
                         recovery_replay_calls=sum(e['phase'] == 'recovery-replay' for e in done))
        calls.extend(dict(arm=arm, phase=e['phase'], **e['trace']) for e in done)
    results = []
    for path in sorted((D/'evaluation').glob('*.json')):
        if not re.fullmatch(r'[AB]-\d+\.json', path.name):
            continue
        obj = read(path)
        review_path = path.with_name(path.stem+'-READING.json')
        review = read(review_path) if review_path.exists() else None
        if review is not None:
            assert review['result_sha256'] == sha(path)
        results.append(dict(model=path.stem, result_sha256=sha(path),
                            summary=obj['summary'], main_assistant_reading=review))
    columns = ['arm', 'phase', 'step', 'targets', 'loss', 'gradient_norm_before_clip',
               'clipping_applied', 'lr', 'EOS_targets', 'role_targets',
               'batch_rows', 'batch_width', 'source_targets']
    with (D/'LOSS_HISTORY.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in calls:
            writer.writerow(dict(row, source_targets=json.dumps(row['source_targets'], sort_keys=True)))
    aggregate = dict(plan_sha256=sha(D/'PLAN.json'), selection_sha256=sha(D/'SERIES_SELECTION.json'),
                     arms=arms, results=results,
                     actual_completed_optimizer_calls=sum(a['actual_completed_calls'] for a in arms.values()),
                     retained_updates=sum(a['receipt']['retained_updates'] for a in arms.values()),
                     retained_targets=sum(a['receipt']['retained_targets'] for a in arms.values()),
                     physical_processed_targets=sum(a['all_physical_processed_targets'] for a in arms.values()),
                     validation_calls=sum(a['validation_calls'] for a in arms.values()),
                     recovery_replay_calls=sum(a['recovery_replay_calls'] for a in arms.values()),
                     corpus_audit=dict(path='DATASET_AUDIT.json',
                                       sha256=sha(D/'DATASET_AUDIT.json'),
                                       note='Build-time audit; actual optimizer counts are reported above.'),
                     formal_adoption=False, independent_human_evaluation=False,
                     all_DEV_exposed=True, sealed_TEST_used=False,
                     scope='Completed calls and retained receipts, not independent data volume. '
                           'EOS/repeat/NLL are automatic; meaning scores come only from linked '
                           'unblinded main-assistant reading, never inferred from automatic metrics.')
    (D/'RESULTS.json').write_text(json.dumps(aggregate, ensure_ascii=False, indent=2)+'\n')
    print({k: aggregate[k] for k in ['actual_completed_optimizer_calls', 'retained_updates',
                                    'retained_targets', 'physical_processed_targets',
                                    'validation_calls', 'recovery_replay_calls']})


if __name__ == '__main__':
    main()
