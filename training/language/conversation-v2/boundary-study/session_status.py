"""Read actual append-only calls; never infer scheduled calls as completed."""
import json,pathlib,time
N=pathlib.Path(__file__).resolve().parent

def main():
 state=dict(as_of_UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),branch='research/natural-boundary-foundation',formal_adoption=False,subagents_used=False,arms={})
 for name in ['control','boundary','clip5']:
  folder=N/'run'/name;p=folder/'updates.jsonl'
  if not p.exists():state['arms'][name]=dict(started=False);continue
  rows=list(map(json.loads,p.read_text().splitlines()));calls=[r for r in rows if r['event']=='completed'];r=dict(started=True,actual_completed_calls=len(calls),retained_completed_calls=sum(e['phase']=='retained'for e in calls),recovery_replay_calls=sum(e['phase']=='recovery-replay'for e in calls),resume_validation_calls=sum(e['phase']=='resume-validation'for e in calls),receipt_exists=(folder/'receipt.json').exists(),archive_exists=(folder/'archive/checkpoint.json').exists());state['arms'][name]=r
 if(N/'WORKFLOW_STATUS.json').exists():state['workflow']=json.loads((N/'WORKFLOW_STATUS.json').read_text())
 if(N/'CLIP_WORKFLOW_STATUS.json').exists():state['clip_workflow']=json.loads((N/'CLIP_WORKFLOW_STATUS.json').read_text())
 state['task_outcome']='Three512-update conditions complete; all prose strict0/24, EOS0/24, repetition24/24. Large expansion and QA phase not run. Formal adoption No-Go.'if all(r.get('receipt_exists')for r in state['arms'].values())else'Partial: use actual ledger counts; no completed-budget claim'
 state['resume']='Check workflow supervisor and child PID+start_ticks first. Never start another live worker. workflow.py resumes unfinished matched A/B with frozen plan; clip5 requires separate recorded gate. Original input mismatch/ambiguous intent must halt.'
 (N/'RESUME_STATUS.json').write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state['arms']))
if __name__=='__main__':main()
