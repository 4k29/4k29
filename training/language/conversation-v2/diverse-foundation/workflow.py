"""One owner process, finite sequential stages. Never autonomously selects by NLL alone."""
import subprocess,os,time
from common import *
def run(script,args,log):
 with (D/log).open('a')as f:
  p=subprocess.run([sys.executable,str(D/script),*args],stdout=f,stderr=subprocess.STDOUT)
 if p.returncode:write(D/'WORKFLOW_FAILURE.json',dict(script=script,args=args,exit_code=p.returncode));raise SystemExit(p.returncode)
def main():
 assert read(D/'PREFLIGHT.json')['pass_all']and read(D/'health/receipt.json')['all_three_exact'];plan=read(D/'PLAN.json');n=plan['comparison_updates'];write(D/'WORKFLOW_STATUS.json',dict(stage='comparison running',pid=os.getpid()))
 for arm in ['A','B']:
  name='initial'+arm
  if not(D/'evaluation'/f'{name}.json').exists():run('evaluate.py',['--model',name],f'eval-{name}.log')
  if not(D/'run'/arm/f'receipt-{n:05d}.json').exists():
   args=['--arm',arm,'--until',str(n)]
   if (D/'run'/arm/'checkpoint.pt').exists():args.append('--resume')
   run('train.py',args,f'train-{arm}.log')
  name=f'{arm}-{n}'
  if not(D/'evaluation'/f'{name}.json').exists():run('evaluate.py',['--model',name],f'eval-{name}.log')
 write(D/'WORKFLOW_STATUS.json',dict(stage='comparison complete, awaiting full-output main-agent reading and fixed-rule selection',actual_comparison_updates_per_arm=n))
if __name__=='__main__':main()
