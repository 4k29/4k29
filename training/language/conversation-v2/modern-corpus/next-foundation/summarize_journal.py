"""Read-only aggregation of actual optimizer calls; never starts training."""
import collections
import json
import pathlib
import statistics

D = pathlib.Path(__file__).resolve().parent
RUN = D.parent / 'private' / 'next-run'


def summarize(path):
    events = []
    for line in path.read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # A live writer may have an unfinished final line; never count it.
            break
    completed = [e for e in events if e['event'] == 'completed']
    phases = {}
    for phase in sorted({e['phase'] for e in completed}):
        rows = [e['trace'] for e in completed if e['phase'] == phase]
        targets = sum(r['targets'] for r in rows)
        source = collections.Counter()
        for row in rows:
            source.update(row['source_targets'])
        gradients = sorted(r['gradient_norm_before_clip'] for r in rows)
        phases[phase] = dict(
            actual_completed_optimizer_calls=len(rows),
            processed_targets=targets,
            target_weighted_loss=sum(r['loss'] * r['targets'] for r in rows) / targets,
            gradient_norm_mean=statistics.mean(gradients),
            gradient_norm_variance=statistics.pvariance(gradients),
            gradient_norm_max=max(gradients),
            clipping_calls=sum(r['clipping_applied'] for r in rows),
            source_targets=dict(source),
            EOS_targets=sum(r['EOS_targets'] for r in rows),
            role_targets=sum(r['role_targets'] for r in rows),
            first_lr=rows[0]['lr'], last_lr=rows[-1]['lr'],
        )
    return dict(phases=phases, actual_completed_calls=len(completed),
                unmatched_intents=sum(e['event'] == 'intent' for e in events) - len(completed),
                scope='Completed journal calls; retained checkpoint cursor is reported separately. '
                      'An unmatched live intent is not counted as a completed update.')


if __name__ == '__main__':
    print(json.dumps({a: summarize(RUN/a/'updates.jsonl') for a in ['A', 'B']}, indent=2))
