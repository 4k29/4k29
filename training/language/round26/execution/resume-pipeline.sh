#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
bash training/language/round26/execution/run.sh --resume >> training/language/round26/execution/train.log 2>&1
python training/language/round26/execution/verify_initial.py
python training/language/round26/execution/audit.py
python training/language/round26/execution/replay_sampler.py
python training/language/round26/execution/verify_paired_exposure.py
python training/language/round26/execution/compare_losses.py
python training/language/round26/execution/decode_training_rollouts.py
bash training/language/round26/execution/compare.sh
python training/language/round26/execution/rebind_old.py
python training/language/round26/execution/check_export_rounding.py
python training/language/round26/execution/diagnose_parity.py
python training/language/round26/execution/diagnose_generation.py
python training/language/round26/execution/diagnose_gap.py
python training/language/round26/execution/measure_repetition.py
python training/language/round26/execution/measure_added_train.py
python training/language/round26/execution/assemble_numerical.py
bash training/language/round26/execution/repository-checks.sh
python training/language/round26/execution/diagnose_sequence_saturation.py
bash training/language/round26/execution/compare_daily.sh
python training/language/round26/execution/check_daily_rounding.py
bash training/language/round26/execution/compare_human_daily.sh
