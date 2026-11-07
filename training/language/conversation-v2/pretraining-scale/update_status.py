import datetime
from common import *
def status():
 arms={}
 for a in ['A','B','C']:
  folder=P/'run'/a;events=list(map(json.loads,(folder/'updates.jsonl').read_text().splitlines()))if(folder/'updates.jsonl').exists()else[];done=[r for r in events if r['event']=='completed'];ret=[r for r in done if r['phase']=='retained'];intents=[r for r in events if r['event']=='intent'];arms[a]=dict(actual_calls=len(done),retained=len(ret),resume_validation=sum(r['phase']=='resume-validation'for r in done),recovery_replay=sum(r['phase']=='recovery-replay'for r in done),ambiguous_intents=len(intents)-len(done),retained_targets=sum(r['trace']['targets']for r in ret),receipt=(folder/'receipt.json').exists())
 o=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),revision=read(P/'PLAN.json')['revision'],arms=arms,excluded_pilot=read(P/'EXCLUDED_PILOT.json'),workflow=read(P/'WORKFLOW_STATUS.json'),formal_adoption=False,subagents_used=False,resume='Check supervisor PID/start time and full-state checkpoint, ledger intents/completions and receipt first. Never repeat completed stage. Explicit --resume only; ambiguous intent halts.',plan_sha256=sha(P/'PLAN.json'))
 write(P/'RESUME_STATUS.json',o);return o
if __name__=='__main__':print(status())
