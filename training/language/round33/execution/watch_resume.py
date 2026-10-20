"""Read-only continuous checkpoint verification; never train or modify checkpoints."""
import datetime, hashlib, json, pathlib, subprocess, sys, time
R = pathlib.Path(__file__).resolve().parents[1]
E = R / 'execution'
REPO = R.parents[2]
last_mtime = None
while True:
    checkpoint = R / 'continue-10000/checkpoint.pt'
    if not checkpoint.exists():
        time.sleep(5)
        continue
    stamp = checkpoint.stat().st_mtime_ns
    if stamp != last_mtime:
        started_stamp = stamp
        result = subprocess.run([sys.executable, str(E / 'inspect_checkpoint.py')], cwd=REPO, text=True, capture_output=True)
        # Retry if trainer atomically replaced the checkpoint while this read-only audit ran.
        if checkpoint.stat().st_mtime_ns != started_stamp:
            continue
        record = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), auditExitCode=result.returncode)
        if result.returncode:
            record['error'] = result.stderr[-4000:]
        else:
            record.update(json.loads(result.stdout))
        with (E / 'continuous-checkpoint-audits.jsonl').open('a') as f:
            f.write(json.dumps(record) + '\n')
        print(json.dumps(record), flush=True)
        last_mtime = started_stamp
        if result.returncode:
            # Record the fault without killing or silently restarting the trainer.
            (E / 'continuous-audit-failure.json').write_text(json.dumps(record, indent=2) + '\n')
            break
        if record['retainedActualUpdates'] == 10000:
            break
    time.sleep(45)
