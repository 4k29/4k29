#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
until test -f training/language/round15/execution/comparison.json; do sleep 55; done
round16_decision=$(python training/language/round16/execution/check_goal.py)
if test "$round16_decision" = skip; then exit 0; fi
if test -f training/language/round16/continue-10000/checkpoint.pt; then
  echo 'Existing Round16 checkpoint: inspect it and use exact --resume; do not rerun this new-run wrapper.' >&2
  exit 1
fi
bash training/language/round16/execution/run.sh > training/language/round16/execution/train.log 2>&1
python training/language/round16/execution/verify_initial.py > training/language/round16/execution/initial-equivalence.log
python training/language/round16/execution/audit.py > training/language/round16/execution/audit.log
python training/language/round16/execution/replay_sampler.py > training/language/round16/execution/replay.log
bash training/language/round16/execution/compare.sh > training/language/round16/execution/comparison-run.log 2>&1
for task in rebind_old check_export_rounding diagnose_parity diagnose_generation diagnose_gap; do
  python "training/language/round16/execution/$task.py" > "training/language/round16/execution/$task.log" 2>&1
done
