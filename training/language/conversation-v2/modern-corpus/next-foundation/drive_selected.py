"""Execute one preregistered selected-arm segment; no semantic auto-scoring."""
import argparse
import datetime
import pathlib
import subprocess
import sys
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from next_runtime import D, N, RUN, read, sha, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--until', type=int, required=True)
    args = parser.parse_args()
    plan = read(D/'PLAN.json')
    assert args.until in [plan['midpoint_updates'], plan['full_pass_updates']]
    selection = read(D/'SERIES_SELECTION.json')
    assert selection['plan_sha256'] == sha(D/'PLAN.json')
    assert selection['common_full_output_review_complete']
    arm = selection['selected_arm']
    assert arm in ['A', 'B']
    if args.until == plan['full_pass_updates']:
        gate = read(D/'MIDPOINT_CONTINUATION_GATE.json')
        assert gate['plan_sha256'] == sha(D/'PLAN.json')
        assert gate['arm'] == arm and gate['approved']
        assert gate['reviewed_step'] == plan['midpoint_updates']
    name = f'{arm}-{args.until}'
    steps = [
        ('training', 'train.py', ['--arm', arm, '--until', str(args.until), '--resume'],
         RUN/arm/f'receipt-{args.until:05d}.json'),
        ('generation', 'evaluate.py', ['--arm', arm, '--step', str(args.until)],
         D/'evaluation'/f'{name}.json'),
        ('content', 'panels.py', ['--model', name], D/'panels'/f'{name}.json'),
        ('context', 'context.py', ['--arm', name], D/'context'/f'{name}.json'),
    ]
    status = dict(arm=arm, until=args.until, plan_sha256=sha(D/'PLAN.json'))
    try:
        for label, script, command, completed in steps:
            if completed.exists():
                # Finished segments are not silently replayed. Main agent checks
                # corresponding receipts/SHA before resuming orchestration.
                print('Existing completion; no replay:', completed, flush=True)
                continue
            status.update(stage=label, status='running',
                          updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
            write(D/'SELECTED_DRIVER_STATUS.json', status)
            log = N/'private'/f'driver-{name}-{label}.log'
            print('START', name, label, flush=True)
            with log.open('a') as out:
                subprocess.run([sys.executable, str(D/script), *command],
                               stdout=out, stderr=subprocess.STDOUT, check=True)
            assert completed.exists()
            print('DONE', name, label, flush=True)
        status.update(status='segment-completed',
                      updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      semantic_review_pending=True)
        write(D/'SELECTED_DRIVER_STATUS.json', status)
    except Exception as error:
        status.update(status='failed', error=repr(error), traceback=traceback.format_exc())
        write(D/'SELECTED_DRIVER_STATUS.json', status)
        raise


if __name__ == '__main__':
    main()
