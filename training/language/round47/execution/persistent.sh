#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../../.."
python training/language/round47/execution/supervise.py "$@"
