# Round36 prospective reproduction

Restore missing SHA-bound source inputs and Round35 paired zero/latest states from lossless parts. Preflight all positive bytes, exact coefficient-only inverse trainer patch, all147986 masks,27 unit tests, real coefficient0.3 gradients, parent Adam/RNG and full initial DEV before freezing/launch. Only resume an incomplete nonrunning checkpoint with execution/run.sh --resume; never relaunch a live or completed run. New auxiliary counters and all exact model/moments/RNG states must be preserved. Same selected/terminal full-output reading and numerical checks; no new TEST, external teacher data, decoding repair or public/site replacement.

## Saved intermediate checkpoints

The active run must remain running; these are recovery instructions for an isolated checkout after an actual interruption. Do not replay or replace any file in the live run.

`execution/retained-paired-200/` and `execution/retained-paired-1000/` contain lossless checkpoint parts, a snapshot receipt, the exact self-generated training trace prefix, and `train-through-snapshot.log`. `resume-evidence.json` binds the log, config, trace, chunk manifest and frozen source manifest by SHA. The recorded validation events exactly equal the checkpoint's internal history. The same evidence is scheduled for actual5000.

Restore missing frozen parent/data references without training:

```bash
python training/language/round36/execution/restore_referenced_chunks.py --manifest training/language/round36/source-manifest.json
```

Restore a saved snapshot, for example actual1000:

```bash
python training/language/round36/checkpoint_chunks.py restore training/language/round36/execution/retained-paired-1000/checkpoint.pt.chunks.json
```

In the isolated, nonrunning recovery checkout, verify `resume-evidence.json` hashes before installing that checkpoint as `continue-10000/checkpoint.pt`, its `training-rollouts.jsonl` as `continue-10000/training-rollouts.jsonl`, and its `train-through-snapshot.log` as `execution/train.log`. Refuse to overwrite any existing run evidence. Preserve the initial checkpoint parts. Do not reset the optimizer, either RNG, counters, best state or the10000 total-update budget. Then the existing guard can resume with:

```bash
bash training/language/round36/execution/run.sh --resume
```

The guard holds an exclusive training lock, requires complete100-step log events through the retained update count, checks all frozen inputs and exact saved config/settings, and restores full optimizer, CPU Torch RNG and private Python RNG. A live or already-completed run must not be launched again. These recovery commands have not been used to interrupt or resume the current run; retaining logs does not perform an optimizer update.
