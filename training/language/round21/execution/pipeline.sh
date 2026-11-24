set -eu
bash training/language/round21/execution/run.sh > training/language/round21/execution/train.log 2>&1
python training/language/round21/execution/verify_initial.py
python training/language/round21/execution/audit.py
python training/language/round21/execution/replay_sampler.py
python training/language/round21/execution/verify_paired_exposure.py
python training/language/round21/execution/compare_losses.py
bash training/language/round21/execution/compare.sh
python training/language/round21/execution/rebind_old.py
python training/language/round21/execution/check_export_rounding.py
python training/language/round21/execution/diagnose_parity.py
python training/language/round21/execution/diagnose_generation.py
python training/language/round21/execution/diagnose_gap.py
