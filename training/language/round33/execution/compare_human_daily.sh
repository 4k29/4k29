#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round33/execution/daily_human_likelihood.py --model training/language/round28/continue-10000/model.js --out training/language/round33/execution/daily-human-old-likelihood.json > training/language/round33/execution/daily-human-old-final.log 2>&1
python training/language/round33/execution/daily_human_likelihood.py --model training/language/round33/continue-10000/model.js --out training/language/round33/execution/daily-human-new-likelihood.json > training/language/round33/execution/daily-human-new-likelihood.log 2>&1
python training/language/round33/execution/assemble_human_daily.py
