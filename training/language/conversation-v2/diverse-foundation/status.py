"""Reconstruct actual work from durable completed-call ledger, never substitute planned budget."""
from common import *
counts={};all_actual=0;all_targets=0
for arm in ['A','B']:
 p=D/'run'/arm/'updates.jsonl'
 if not p.exists():continue
 events=[json.loads(l)for l in p.read_text().splitlines()];done=[r for r in events if r['event']=='completed'];kept={r['step']:r['trace']for r in done if r['phase']=='retained'};counts[arm]=dict(actual_optimizer_calls=len(done),retained_updates=len(kept),retained_targets=sum(r['targets']for r in kept.values()),resume_validation_calls=sum(r['phase']=='resume-validation'for r in done),recovery_replay_calls=sum(r['phase']=='recovery-replay'for r in done),ambiguous_intents=len([r for r in events if r['event']=='intent'])-len(done));all_actual+=len(done);all_targets+=sum(r['trace']['targets']for r in done)
health=read(D/'health/receipt.json');write(D/'RESUME_STATUS.json',dict(phase=read(D/'WORKFLOW_STATUS.json')['stage'],actual_optimizer_calls_including_health=all_actual+health['actual_optimizer_calls'],actual_processed_targets_including_replay_and_health=all_targets+health['retained_targets'],main=counts,health=health,branch='research/diverse-japanese-foundation',draft_PR='https://github.com/4k29/4k29/pull/104',training_started=True,source_corpus_sha256=sha(D/'corpus.jsonl.gz'),plan_sha256=sha(D/'PLAN.json'),formal_adoption='No-Go',public_model_changed=False,sealed_TEST_used=False,subagents_used=0,next='follow frozen comparison selection then one-pass continuation; check receipts before rerun'))
print(read(D/'RESUME_STATUS.json'))
