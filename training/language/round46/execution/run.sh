#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round46/execution/execute.py "$@"
