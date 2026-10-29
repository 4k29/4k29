import datetime
from common import *
def completed(path):return[r for r in map(json.loads,path.read_text().splitlines())if r['event']=='completed']if path.exists()else[]
old=completed(P/'run/A/updates-v2.jsonl');new=completed(P/'run/A/updates-clean.jsonl');arms={}
for a in ['B','C']:
 d=completed(P/'run'/a/'updates.jsonl');arms[a]=dict(actual_calls=len(d),retained=512,resume_validation=2,retained_targets=351219,complete=True)
cur=max([512]+[r['step']for r in new]);arms['A']=dict(actual_calls=len(old)+len(new),original_v2_calls=len(old),clean_calls=len(new),retained_unique_updates=cur,recovery_replay_calls=sum(r['phase']=='recovery-replay'for r in new),resume_validation_calls=2+sum(r['phase']=='resume-validation'for r in new),excluded_tail_updates=28,retained_trace_targets=sum(r['trace']['targets']for r in old if r['phase']=='retained'and r['step']<=512)+sum(r['trace']['targets']for r in new if r['phase']!='resume-validation'),complete=(P/'run/A/receipt.json').exists())
r=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),stage=read(P/'CONTINUATION_STATUS.json'),arms=arms,source_family_fix=read(P/'FAMILY_EXCLUSION_FIX.json'),excluded_pilot=read(P/'EXCLUDED_PILOT.json'),overfit=read(P/'overfit/receipt.json'),formal_adoption=False,subagents_used=False,clean_plan_sha256=sha(P/'CLEAN_PLAN.json'),resume='Use continue_clean.py only. Check live supervisor PID/start_ticks, receipts and full-state checkpoint before resuming. Original train.py and continue_workflow.py are superseded for A continuation; they must not restart completed comparison or excluded suffix.')
write(P/'RESUME_STATUS.json',r);print(dict(UTC=r['UTC'],stage=r['stage']['stage'],A=arms['A']))
