#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../../.."
python training/language/round10/evaluate.py --model training/language/round11/continue-10000/model.js --partition validation --out training/language/round14/execution/old-validation.json --reference > training/language/round14/execution/old-generation.log 2>&1 || exit $?
python training/language/round10/evaluate.py --model training/language/round14/continue-10000/model.js --partition validation --out training/language/round14/execution/new-validation.json --reference > training/language/round14/execution/new-generation.log 2>&1 || exit $?
# Both statuses are retained: a parity failure must not erase the other report.
node training/language/round10/evaluate_js.mjs "$PWD/training/language/round11/continue-10000/model.js" training/language/round14/execution/old-validation.json training/language/round14/execution/old-validation-js.json > training/language/round14/execution/old-parity.log 2>&1
old_status=$?
node training/language/round10/evaluate_js.mjs "$PWD/training/language/round14/continue-10000/model.js" training/language/round14/execution/new-validation.json training/language/round14/execution/new-validation-js.json > training/language/round14/execution/new-parity.log 2>&1
new_status=$?
printf '{"oldParityExit":%d,"newParityExit":%d}\n' "$old_status" "$new_status" > training/language/round14/execution/parity-status.json
