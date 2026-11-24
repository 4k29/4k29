"""Detached finite comparison only. Selection/continuation require saved explicit research decision."""
import subprocess,os,datetime,fcntl
from common import P,write,read,sha,ROOT
lock=(P/'supervisor.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def run(cmd,log):
 write(P/'WORKFLOW_STATUS.json',dict(supervisor=os.getpid(),stage=cmd,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 with(P/log).open('ab')as f:subprocess.run([sys.executable,str(P/cmd[0])]+cmd[1:],stdout=f,stderr=subprocess.STDOUT,check=True)
import sys
for arm in ['A','B','C']:
 folder=P/'run'/arm;receipt=folder/'receipt-0512.json'
 if not receipt.exists():
  args=['train.py','--arm',arm,'--until','512']
  if(folder/'updates.jsonl').exists():args+=['--resume']
  run(args,'training-'+arm+'.log')
 if not(P/'evaluation'/(arm+'-0512.json')).exists():run(['evaluate.py','--arm',arm,'--label',arm+'-0512'],'evaluation-'+arm+'.log')
write(P/'WORKFLOW_STATUS.json',dict(supervisor=os.getpid(),stage='COMPARISON_COMPLETE_NEEDS_FROZEN_SELECTION',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
