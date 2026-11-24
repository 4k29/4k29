set -eu
node --test tests/*.test.mjs > training/language/round34/execution/repository-tests.log 2>&1
node evaluation/evaluate-japanese.mjs > training/language/round34/execution/public-evaluation.log 2>&1
node --check docs/app.js
