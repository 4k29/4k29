set -eu
bash training/language/round32/execution/run.sh "$@"
python training/language/round32/execution/verify_initial.py
python training/language/round32/execution/audit.py
python training/language/round32/execution/replay_sampler.py
python training/language/round32/execution/verify_paired_exposure.py
python training/language/round32/execution/compare_losses.py
python training/language/round32/execution/decode_training_rollouts.py
bash training/language/round32/execution/compare.sh
python training/language/round32/execution/rebind_old.py
python training/language/round32/execution/check_export_rounding.py
python training/language/round32/execution/diagnose_parity.py
python training/language/round32/execution/diagnose_generation.py
python training/language/round32/execution/diagnose_gap.py
python training/language/round32/execution/measure_repetition.py
python training/language/round32/execution/measure_added_train.py
python training/language/round32/execution/assemble_numerical.py
bash training/language/round32/execution/repository-checks.sh
python training/language/round32/execution/diagnose_sequence_saturation.py
bash training/language/round32/execution/compare_daily.sh
python training/language/round32/execution/check_daily_rounding.py
bash training/language/round32/execution/compare_human_daily.sh
python training/language/round32/execution/verify_best_archive.py

python training/language/round32/execution/content-native-dev/evaluate.py --model training/language/round32/continue-10000/model.js --out training/language/round32/execution/content-native-dev/new-python.json > training/language/round32/execution/content-native-dev/new-generation.log 2>&1
node training/language/round10/evaluate_js.mjs "$PWD/training/language/round32/continue-10000/model.js" training/language/round32/execution/content-native-dev/new-python.json training/language/round32/execution/content-native-dev/new-javascript.json > training/language/round32/execution/content-native-dev/new-parity.log 2>&1
