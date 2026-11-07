#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round33/execution/execute.py "$@"
