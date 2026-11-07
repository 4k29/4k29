#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../../.."
bash training/language/round22/execution/pipeline.sh > training/language/round22/execution/pipeline.log 2>&1
pipeline_status=$?
python training/language/round22/execution/publish_mechanical.py "$pipeline_status" > training/language/round22/execution/automatic-publish.log 2>&1
