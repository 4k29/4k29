set -eu
bash training/language/round17/execution/run.sh > training/language/round17/execution/train.log 2>&1
python training/language/round17/execution/verify_initial.py
python training/language/round17/execution/audit.py
python training/language/round17/execution/replay_sampler.py
bash training/language/round17/execution/compare.sh
python training/language/round17/execution/rebind_old.py
python training/language/round17/execution/check_export_rounding.py
python training/language/round17/execution/diagnose_parity.py
python training/language/round17/execution/diagnose_generation.py
python training/language/round17/execution/diagnose_gap.py
