#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round27/execution/daily_human_likelihood.py --model training/language/round25/continue-10000/model.js --out training/language/round27/execution/daily-human-old-likelihood.json --reuse-exact > training/language/round27/execution/daily-human-old-final.log 2>&1
python training/language/round27/execution/daily_human_likelihood.py --model training/language/round27/continue-10000/model.js --out training/language/round27/execution/daily-human-new-likelihood.json > training/language/round27/execution/daily-human-new-likelihood.log 2>&1
python training/language/round27/execution/assemble_human_daily.py
