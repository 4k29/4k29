set -eu
bash training/language/round44/execution/run.sh "$@"
python training/language/round44/execution/verify_initial.py
python training/language/round44/execution/audit.py
python training/language/round44/execution/replay_sampler.py
python training/language/round44/execution/paired_training_audit.py
python training/language/round44/execution/audit_eos_exposure.py
python training/language/round44/execution/compare_losses.py
python training/language/round44/execution/decode_training_rollouts.py
bash training/language/round44/execution/compare.sh
python training/language/round44/execution/rebind_old.py
python training/language/round44/execution/check_export_rounding.py
python training/language/round44/execution/diagnose_parity.py
python training/language/round44/execution/diagnose_generation.py
python training/language/round44/execution/diagnose_gap.py
python training/language/round44/execution/measure_repetition.py
python training/language/round44/execution/assemble_numerical.py
bash training/language/round44/execution/repository-checks.sh
python training/language/round44/execution/diagnose_sequence_saturation.py
bash training/language/round44/execution/compare_daily.sh
python training/language/round44/execution/check_daily_rounding.py
bash training/language/round44/execution/compare_human_daily.sh
python training/language/round44/execution/verify_best_archive.py
python training/language/round44/execution/content-native-dev/evaluate.py --model training/language/round43/continue-10000/model.js --out training/language/round44/execution/content-native-dev/old-python.json > training/language/round44/execution/content-native-dev/old-generation.log 2>&1
node training/language/round10/evaluate_js.mjs "$PWD/training/language/round43/continue-10000/model.js" training/language/round44/execution/content-native-dev/old-python.json training/language/round44/execution/content-native-dev/old-javascript.json > training/language/round44/execution/content-native-dev/old-parity.log 2>&1
python training/language/round44/execution/check_final_native_rounding.py --snapshot training/language/round43/continue-10000 --generation training/language/round44/execution/content-native-dev/old-python.json --out training/language/round44/execution/content-native-dev/old-rounding.json > training/language/round44/execution/content-native-dev/old-rounding.log 2>&1
python training/language/round44/execution/content-native-dev/evaluate.py --model training/language/round44/continue-10000/model.js --out training/language/round44/execution/content-native-dev/new-python.json > training/language/round44/execution/content-native-dev/new-generation.log 2>&1
node training/language/round10/evaluate_js.mjs "$PWD/training/language/round44/continue-10000/model.js" training/language/round44/execution/content-native-dev/new-python.json training/language/round44/execution/content-native-dev/new-javascript.json > training/language/round44/execution/content-native-dev/new-parity.log 2>&1
python training/language/round44/execution/check_final_native_rounding.py --snapshot training/language/round44/continue-10000 --generation training/language/round44/execution/content-native-dev/new-python.json --out training/language/round44/execution/content-native-dev/new-rounding.json > training/language/round44/execution/content-native-dev/new-rounding.log 2>&1
