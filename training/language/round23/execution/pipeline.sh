set -eu
bash training/language/round23/execution/run.sh > training/language/round23/execution/train.log 2>&1
python training/language/round23/execution/verify_initial.py
python training/language/round23/execution/audit.py
python training/language/round23/execution/replay_sampler.py
bash training/language/round23/execution/compare.sh
python training/language/round23/execution/rebind_old.py
python training/language/round23/execution/check_export_rounding.py
python training/language/round23/execution/diagnose_parity.py
python training/language/round23/execution/diagnose_generation.py
python training/language/round23/execution/diagnose_gap.py
