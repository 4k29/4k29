set -eu
bash training/language/round18/execution/run.sh > training/language/round18/execution/train.log 2>&1
python training/language/round18/execution/verify_initial.py
python training/language/round18/execution/audit.py
python training/language/round18/execution/replay_sampler.py
bash training/language/round18/execution/compare.sh
python training/language/round18/execution/rebind_old.py
python training/language/round18/execution/check_export_rounding.py
python training/language/round18/execution/diagnose_parity.py
python training/language/round18/execution/diagnose_generation.py
python training/language/round18/execution/diagnose_gap.py
