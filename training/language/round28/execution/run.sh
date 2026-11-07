#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round28/execution/execute.py "$@"
