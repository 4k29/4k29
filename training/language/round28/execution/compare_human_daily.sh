#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round28/execution/daily_human_likelihood.py --model training/language/round25/continue-10000/model.js --out training/language/round28/execution/daily-human-old-likelihood.json --reuse-exact > training/language/round28/execution/daily-human-old-final.log 2>&1
python training/language/round28/execution/daily_human_likelihood.py --model training/language/round28/continue-10000/model.js --out training/language/round28/execution/daily-human-new-likelihood.json > training/language/round28/execution/daily-human-new-likelihood.log 2>&1
python training/language/round28/execution/assemble_human_daily.py
