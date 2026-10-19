#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round16/train.py --merges 512 --steps 10000 --dim 192 --layers 8 --heads 4 --batch 8 --threads 2 --seed 2049 --lr 2.2499999999999998e-05 --validation-every 500 --run continue-10000 --precision float32 "$@"
