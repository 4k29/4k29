"""Finite preregistered baseline/common-budget execution; no semantic auto-selection.
The main agent reviews full outputs before selecting continuation. No sub-agents/APIs.
"""
import pathlib,sys,subprocess,datetime,traceback
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
from next_runtime import *

def run(label,script,args,completion):
 if completion.exists():
  print('Verified completed stage retained:',label,flush=True);return
 status=dict(stage=label,status='running',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(D/'PLAN.json'));write(D/'DRIVER_STATUS.json',status);print('START',label,flush=True);log=N/'private'/('driver-'+label+'.log')
 with log.open('a')as out:subprocess.run([sys.executable,str(D/script),*args],stdout=out,stderr=subprocess.STDOUT,check=True)
 assert completion.exists(),label;status.update(status='completed',finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());write(D/'DRIVER_STATUS.json',status);print('DONE',label,flush=True)

def main():
 plan=read(D/'PLAN.json');boundary=plan['comparison_updates']
 for arm in ['A','B']:
  proof=read(RUN/arm/'RESUME_AUDIT.json');assert proof['exact_model_adam_torch_privatePython_globalPython_numpy_sampler_cursor_trace_after_actual2_to4']
 try:
  for arm in ['A','B']:run(arm+'-initial-generation','evaluate.py',['--arm',arm,'--step','0'],D/'evaluation'/f'{arm}-0.json')
  for arm in ['A','B']:
   run(arm+'-common-training','train.py',['--arm',arm,'--until',str(boundary),'--resume'],RUN/arm/f'receipt-{boundary:05d}.json')
   run(arm+'-common-generation','evaluate.py',['--arm',arm,'--step',str(boundary)],D/'evaluation'/f'{arm}-{boundary}.json')
   run(arm+'-common-content','panels.py',['--model',f'{arm}-{boundary}'],D/'panels'/f'{arm}-{boundary}.json')
   run(arm+'-common-context','context.py',['--arm',f'{arm}-{boundary}'],D/'context'/f'{arm}-{boundary}.json')
  write(D/'COMMON_COMPARISON_COMPLETE.json',dict(complete=True,plan_sha256=sha(D/'PLAN.json'),arms={a:read(RUN/a/f'receipt-{boundary:05d}.json')for a in ['A','B']},main_agent_semantic_selection_pending=True,formal_adoption=False));print('COMMON BUDGET COMPLETE; awaiting main-agent full generation reading',flush=True)
 except Exception as error:
  old=read(D/'DRIVER_STATUS.json');old.update(status='failed',error=repr(error),traceback=traceback.format_exc());write(D/'DRIVER_STATUS.json',old);raise
if __name__=='__main__':main()
