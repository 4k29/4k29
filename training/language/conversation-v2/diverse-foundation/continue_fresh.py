"""Preregistered secondary fresh completion after primary failure; no new epoch or policy tuning."""
import argparse,subprocess,shutil,os
from common import *
from restore_checkpoint import restore

def main():
 a=argparse.ArgumentParser();a.add_argument('--until',type=int,required=True);args=a.parse_args();plan=read(D/'PLAN.json');proto=read(D/'FRESH_COMPLETION_PROTOCOL.json');assert not read(D/'TERMINAL_REVIEW.json')['primary_language_success'];assert args.until in [plan['midpoint_updates'],plan['full_pass_updates']]
 for r in read(D/'DEPENDENCIES.json'):assert sha(ROOT/r['path'])==r['sha256']
 if args.until==plan['full_pass_updates']:assert read(D/'B_MIDPOINT_REVIEW.json')['continue_frozen_pass']
 out=D/'run/B';raw=out/'checkpoint.pt'
 if not raw.exists():
  manifests=sorted(out.glob('archive-*/checkpoint.json'),key=lambda p:read(p)['active_cursor']);restore(manifests[-1],raw)
 obj=torch.load(raw,weights_only=False);assert obj['arm']=='B'and obj['plan_sha256']==sha(D/'PLAN.json');assert proto['start_cursor']<=obj['active_cursor']<=args.until
 if obj['active_cursor']==proto['start_cursor']:assert sha(raw)==proto['initial_B_checkpoint_sha256'];assert shutil.disk_usage(D).free>=proto['minimum_free_bytes_before_secondary']
 write(D/'FRESH_STATUS.json',dict(stage='secondary fresh completion running',until=args.until,starting_cursor=obj['active_cursor'],pid=os.getpid(),free_bytes=shutil.disk_usage(D).free,primary_selected_arm_unchanged='A'))
 if not(out/f'receipt-{args.until:05d}.json').exists():
  with(D/f'continuation-B-{args.until}.log').open('a')as f:subprocess.run([sys.executable,str(D/'train.py'),'--arm','B','--until',str(args.until),'--resume'],stdout=f,stderr=subprocess.STDOUT,check=True)
 label=f'B-{args.until}'
 if not(D/'evaluation'/f'{label}.json').exists():
  with(D/f'eval-{label}.log').open('a')as f:subprocess.run([sys.executable,str(D/'evaluate.py'),'--model',label],stdout=f,stderr=subprocess.STDOUT,check=True)
 write(D/'FRESH_STATUS.json',dict(stage='secondary fresh milestone complete, full reading required',cursor=args.until,full_pass_complete=args.until==plan['full_pass_updates'],primary_selected_arm_unchanged='A'))
if __name__=='__main__':main()
