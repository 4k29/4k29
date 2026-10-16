# User-requested pause

R26 stopped cleanly after **3,099 actual additional optimizer updates**, not 10,000. AdamW counters are 13,099. The requested stop arrived after the 3,000-update validation had completed and training had advanced. No updates were discarded or replayed.

Best exposed-development NLL/UTF-8 byte is **0.9695510136979912 at update 3,000**, versus R25 best 0.9714220852387883. This is a loss diagnostic only: R26 autoregressive language evaluation and Python/JavaScript generation comparison have **not** been performed. Strict language gates are unassessed. No new TEST was generated, no public model changed, and R27 training has not started.

`continue-10000/checkpoint.pt` contains the latest model, matching AdamW moments/counters, Torch RNG, private Python RNG, best model state, validation history and exposure/rollout counters. Selected export is the best-at-3,000 state; resume from the **latest checkpoint**, never selected weights with latest optimizer. Inspection confirmed finite weights/moments, unchanged trainer SHA and all 309 retained rollout records matching counters (15,144 generated tokens, 5,688 negative positions). Training and validation logs are preserved.

## Exact continuation when requested

From the repository root, with no other trainer running:

```bash
python training/language/round26/execution/inspect_checkpoint.py
bash training/language/round26/execution/run.sh --resume >> training/language/round26/execution/train.log 2>&1
```

The fixed target remains 10,000 total additional updates; **6,901 remain**. `--resume` checks frozen settings/config/data/code identity and restores all saved states. Append to the existing log; do not overwrite it or run without `--resume`. The `execution/user-pause-requested` marker makes the detached pipeline stop after checkpoint inspection rather than invoking completion-only evaluations. After a future training completion, run the evaluation commands in `execution/pipeline.sh` starting with `verify_initial.py`, without re-running its training command. Full evaluation and actual reading of all generated text remain required before any language claim or adoption.
