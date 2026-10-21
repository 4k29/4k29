#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round35/execution/execute.py "$@"
