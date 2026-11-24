#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
for n in 13 14 15; do
  bash "training/language/round$n/execution/run.sh" > "training/language/round$n/execution/train.log" 2>&1
  python "training/language/round$n/execution/audit.py" > "training/language/round$n/execution/audit.log"
  python "training/language/round$n/execution/replay_sampler.py" > "training/language/round$n/execution/replay.log"
  bash "training/language/round$n/execution/compare.sh" > "training/language/round$n/execution/comparison-run.log" 2>&1 &
done
wait
