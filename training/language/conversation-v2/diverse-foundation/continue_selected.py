"""Execute one fixed continuation milestone, then return for full-output/regression review."""
import argparse,subprocess
from common import *
from restore_checkpoint import restore

def main():
 for r in read(D/'DEPENDENCIES.json'):assert sha(ROOT/r['path'])==r['sha256'],r['path']
 a=argparse.ArgumentParser();a.add_argument('--until',type=int,required=True);args=a.parse_args();plan=read(D/'PLAN.json');selection=read(D/'SELECTION.json');arm=selection['selected_arm'];assert args.until in [plan['midpoint_updates'],plan['full_pass_updates']];assert selection['rule_unchanged'];out=D/'run'/arm;raw=out/'checkpoint.pt'
 if not raw.exists():restore(out/f"archive-{plan['comparison_updates']:05d}"/'checkpoint.json',raw)
 if args.until==plan['full_pass_updates']:assert read(D/'MIDPOINT_REVIEW.json')['continue_frozen_pass']and read(D/'MIDPOINT_REVIEW.json')['not_extra_epoch']
 if not(out/f'receipt-{args.until:05d}.json').exists():
  with(D/f'continuation-{arm}-{args.until}.log').open('a')as f:subprocess.run([sys.executable,str(D/'train.py'),'--arm',arm,'--until',str(args.until),'--resume'],stdout=f,stderr=subprocess.STDOUT,check=True)
 label=f'{arm}-{args.until}'
 if not(D/'evaluation'/f'{label}.json').exists():
  with(D/f'eval-{label}.log').open('a')as f:subprocess.run([sys.executable,str(D/'evaluate.py'),'--model',label],stdout=f,stderr=subprocess.STDOUT,check=True)
 write(D/'CONTINUATION_STATUS.json',dict(completed_milestone=args.until,selected_arm=arm,full_pass_complete=args.until==plan['full_pass_updates'],pending='full-output review before any further work'))
if __name__=='__main__':main()
