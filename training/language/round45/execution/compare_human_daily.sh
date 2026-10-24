#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round45/execution/daily_human_likelihood.py --model training/language/round44/continue-10000/model.js --out training/language/round45/execution/daily-human-old-likelihood.json > training/language/round45/execution/daily-human-old-final.log 2>&1
python training/language/round45/execution/daily_human_likelihood.py --model training/language/round45/continue-10000/model.js --out training/language/round45/execution/daily-human-new-likelihood.json > training/language/round45/execution/daily-human-new-likelihood.log 2>&1
python training/language/round45/execution/assemble_human_daily.py
