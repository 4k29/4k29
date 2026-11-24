#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../../.."
bash training/language/round26/execution/resume-pipeline.sh > training/language/round26/execution/resume-pipeline.log 2>&1
status=$?
python training/language/round26/execution/publish_mechanical.py "$status" > training/language/round26/execution/resume-publish.log 2>&1
