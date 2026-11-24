"""Exactly one fixed data pass of the preregistered selected arm, with saved milestone evaluations."""
import subprocess,os,sys,datetime,fcntl
from common import *
lock=(P/'supervisor.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);plan=read(P/'PLAN.json');decision=read(P/'SELECTION.json');assert decision['plan_sha256']==sha(P/'PLAN.json')and decision['comparison_all_complete']and decision['chosen_arm']in ['A','B','C'];arm=decision['chosen_arm'];out=P/'run'/arm
for a in ['A','B','C']:assert(P/'run'/a/'receipt-0512.json').exists()
def run(args,log):
 write(P/'CONTINUATION_STATUS.json',dict(supervisor=os.getpid(),stage=args,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),fixed_final_targets=plan['full_pass_targets']))
 with(P/log).open('ab')as f:subprocess.run([sys.executable,str(P/args[0])]+args[1:],stdout=f,stderr=subprocess.STDOUT,check=True)
# Detached finite execution; no automatic selection rule changes or extra epoch.
if not(P/'overfit/receipt.json').exists():run(['overfit.py'],'overfit.log')
for arm0,label in [('initial','initial3470'),('fresh','initial-fresh')]:
 if not(P/'evaluation'/(label+'.json')).exists():run(['evaluate.py','--arm',arm0,'--label',label],'baseline-'+label+'.log')
if not(P/'parity-summary.json').exists():run(['parity_check.py','--models',arm],'parity.log')
for end in [1024,1536,2048,2560,plan['full_pass_updates']]:
 receipt=out/('receipt-%04d.json'%end)
 if not receipt.exists():run(['train.py','--arm',arm,'--until',str(end),'--resume'],'continuation-'+arm+'.log')
 label=arm+'-%04d'%end
 if not(P/'evaluation'/(label+'.json')).exists():run(['evaluate.py','--arm',arm,'--label',label],'evaluation-'+label+'.log')
 summary=read(P/'evaluation'/(label+'-summary.json'))
 # Record any mechanical regression; fixed pass does not authorize another budget/epoch.
 write(P/'LAST_MILESTONE.json',dict(label=label,summary=summary,formal_adoption=False,no_extra_epoch_authorized=True))
if not(P/'evaluation'/(arm+'.json')).exists():run(['evaluate_panels.py','--model',arm],'evaluation-panels.log')
write(P/'CONTINUATION_STATUS.json',dict(supervisor=os.getpid(),stage='FINITE_ONE_PASS_COMPLETE',selected_arm=arm,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),formal_adoption=False))
