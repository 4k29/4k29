"""Finite zero-update evaluation jobs; skip only complete artifacts, never generate replacement answers."""
import argparse,subprocess
from common import *
def run(script,args,log):
 with(D/log).open('a')as f:subprocess.run([sys.executable,str(D/script),*args],stdout=f,stderr=subprocess.STDOUT,check=True)
def main():
 a=argparse.ArgumentParser();a.add_argument('--models',nargs='+',required=True);args=a.parse_args()
 if not(D/'CONTEXT_ABLATION_PROTOCOL.json').exists():run('context.py',['--freeze'],'context-freeze.log')
 for name in args.models:
  if not(D/'panels'/f'{name}.json').exists():run('evaluate_panels.py',['--model',name],f'panels-{name}.log')
  if not(D/'probabilities'/f'{name}.json').exists():run('diagnose.py',['--arm',name,'--label',name],f'probabilities-{name}.log')
  if not(D/'context'/f'{name}.json').exists():run('context.py',['--arm',name],f'context-{name}.log')
  if not(D/'fit'/f'{name}.json').exists():run('fit_diagnostic.py',['--model',name],f'fit-{name}.log')
  if not(D/'sampling'/f'{name}.json').exists():run('sample_aux.py',['--model',name],f'sampling-{name}.log')
  if not(D/'daily-prose'/f'{name}.json').exists():run('daily_aux.py',['--model',name],f'daily-{name}.log')
 if not(D/'parity-terminal-summary.json').exists():run('parity_terminal.py',['--models',*args.models],'parity-terminal.log')
 else:
  known=read(D/'parity-terminal-summary.json')
  for name in args.models:
   if name not in known and not(D/f'parity-{name}-summary.json').exists():run('parity_terminal.py',['--models',name,'--tag',name],f'parity-{name}.log')
 write(D/('POST_COMPLETED_'+'_'.join(args.models)+'.json'),dict(models=args.models,optimizer_updates=0,manual_semantic_review_required=True))
if __name__=='__main__':main()
