#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../../.."
bash training/language/round20/execution/pipeline.sh > training/language/round20/execution/pipeline.log 2>&1
pipeline_status=$?
python training/language/round20/execution/publish_mechanical.py "$pipeline_status" > training/language/round20/execution/automatic-publish.log 2>&1
