#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../../.."
python training/language/round39/execution/evaluate_daily.py --model training/language/round38/continue-10000/model.js --out training/language/round39/execution/daily-old-python.json --reuse-exact > training/language/round39/execution/daily-old-generation.log 2>&1 || exit $?
python training/language/round39/execution/evaluate_daily.py --model training/language/round39/continue-10000/model.js --out training/language/round39/execution/daily-new-python.json > training/language/round39/execution/daily-new-generation.log 2>&1 || exit $?
node training/language/round10/evaluate_js.mjs "$PWD/training/language/round38/continue-10000/model.js" training/language/round39/execution/daily-old-python.json training/language/round39/execution/daily-old-javascript.json > training/language/round39/execution/daily-old-parity.log 2>&1
old_status=$?
node training/language/round10/evaluate_js.mjs "$PWD/training/language/round39/continue-10000/model.js" training/language/round39/execution/daily-new-python.json training/language/round39/execution/daily-new-javascript.json > training/language/round39/execution/daily-new-parity.log 2>&1
new_status=$?
printf '{"oldParityExit":%d,"newParityExit":%d}\n' "$old_status" "$new_status" > training/language/round39/execution/daily-parity-status.json
python training/language/round39/execution/assemble_daily.py || exit $?
if [ "$old_status" -ne 0 ] || [ "$new_status" -ne 0 ]; then exit 1; fi
