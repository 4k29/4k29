#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round39/execution/daily_human_likelihood.py --model training/language/round38/continue-10000/model.js --out training/language/round39/execution/daily-human-old-likelihood.json > training/language/round39/execution/daily-human-old-final.log 2>&1
python training/language/round39/execution/daily_human_likelihood.py --model training/language/round39/continue-10000/model.js --out training/language/round39/execution/daily-human-new-likelihood.json > training/language/round39/execution/daily-human-new-likelihood.log 2>&1
python training/language/round39/execution/assemble_human_daily.py
