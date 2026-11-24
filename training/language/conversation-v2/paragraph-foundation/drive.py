"""Run only the finite preregistered comparison. No semantic adoption or extra epochs."""
import subprocess,datetime,traceback
from study_runtime import *

def run(label,script,args,completion):
 if completion.exists():
  print('Retained completed stage',label,flush=True);return
 state=dict(stage=label,status='running',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'));write(P/'DRIVER_STATUS.json',state);print('START',label,flush=True)
 with(P/'private'/('driver-'+label+'.log')).open('a')as log:subprocess.run([sys.executable,str(P/script),*args],stdout=log,stderr=subprocess.STDOUT,check=True)
 assert completion.exists(),('Missing completion artifact',label);state.update(status='completed',finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());write(P/'DRIVER_STATUS.json',state);print('DONE',label,flush=True)

def main():
 plan=read(P/'PLAN.json');assert read(P/'PREFLIGHT.json')['pass_all'];assert(P/'evaluation/base-0.json').exists(),'Base generation must finish first'
 try:
  run('baseline-content','panels.py',['--model','base-0'],P/'panels/base-0.json')
  run('baseline-new-TRAIN-probes','train_probes.py',['--model','base-0'],P/'train-probes/base-0.json')
  run('baseline-parity','parity_check.py',['--models','base-0','--tag','baseline'],P/'parity-baseline-summary.json')
  previous={a:0 for a in ['A','B']}
  for end in plan['checkpoints']:
   for arm in ['A','B']:
    if previous[arm] and not(DURABLE/arm/'checkpoint.pt').exists():
     subprocess.run([sys.executable,str(P/'stage_checkpoint.py'),arm+'-'+str(previous[arm]),'--restore'],check=True)
    args=['--arm',arm,'--until',str(end)]+(['--resume']if previous[arm]else[])
    run(arm+'-'+str(end)+'-training','train.py',args,P/'private/run'/arm/f'receipt-{end:05d}.json')
    run(arm+'-'+str(end)+'-archive','stage_checkpoint.py',[arm+'-'+str(end)],P/'receipts'/(arm+'-'+str(end)+'-GIT_RESTORE_PROOF.json'))
    previous[arm]=end
    if end>4:
     name=arm+'-'+str(end);run(name+'-generation','evaluate.py',['--model',name],P/'evaluation'/(name+'.json'));run(name+'-content','panels.py',['--model',name],P/'panels'/(name+'.json'));run(name+'-TRAIN-probes','train_probes.py',['--model',name],P/'train-probes'/(name+'.json'))
  run('terminal-parity','parity_check.py',['--models','A-'+str(plan['updates_per_arm']),'B-'+str(plan['updates_per_arm']),'--tag','terminal'],P/'parity-terminal-summary.json')
  write(P/'FINITE_COMPARISON_COMPLETE.json',dict(complete=True,plan_sha256=sha(P/'PLAN.json'),arms={a:read(P/'receipts'/(a+'-'+str(plan['updates_per_arm'])+'.json'))for a in ['A','B']},semantic_full_output_review_pending=True,extra_epochs=0,formal_adoption=False));print('All fixed training/evaluation stages complete; main-agent full-output interpretation remains',flush=True)
 except Exception as error:
  status=read(P/'DRIVER_STATUS.json');status.update(status='failed',error=repr(error),traceback=traceback.format_exc());write(P/'DRIVER_STATUS.json',status);raise
if __name__=='__main__':main()
