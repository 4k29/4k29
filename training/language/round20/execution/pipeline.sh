set -eu
bash training/language/round20/execution/run.sh > training/language/round20/execution/train.log 2>&1
python training/language/round20/execution/verify_initial.py
python training/language/round20/execution/audit.py
python training/language/round20/execution/replay_sampler.py
python training/language/round20/execution/verify_paired_exposure.py
python training/language/round20/execution/compare_losses.py
bash training/language/round20/execution/compare.sh
python training/language/round20/execution/rebind_old.py
python training/language/round20/execution/check_export_rounding.py
python training/language/round20/execution/diagnose_parity.py
python training/language/round20/execution/diagnose_generation.py
python training/language/round20/execution/diagnose_gap.py
