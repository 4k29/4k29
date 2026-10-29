"""Run only after finite clean training and fixed primary/panel evaluation complete. No optimizer calls."""
import subprocess,sys,os
from common import *
assert read(P/'CONTINUATION_STATUS.json')['stage']=='FINITE_ONE_PASS_COMPLETE';assert read(P/'run/A/receipt.json')['retained_updates']==2966

def run(args,log):
 with(P/log).open('ab')as f:subprocess.run([sys.executable,str(P/args[0])]+args[1:],stdout=f,stderr=subprocess.STDOUT,check=True)
for arm,label in [('initial','initial3470'),('A','A-2966')]:
 if not(P/'probabilities'/(label+'.json')).exists():run(['diagnose_final.py','--arm',arm,'--label',label],'probabilities-'+label+'.log')
for arm in ['initial','A']:
 if not(P/'context'/(arm+'.json')).exists():run(['context_ablation.py','--arm',arm],'context-'+arm+'.log')
if not(P/'parity-terminal-summary.json').exists():run(['parity_terminal.py','--models','A'],'parity-terminal.log')
run(['render_outputs.py'],'render.log')
# All fixed complete milestones; rolling128 operational snapshots are not all retained forever.
from archive_states import archive
for n in [1024,1536,2048,2560]:
 raw=P/'run/A'/('checkpoint-%04d.pt'%n);out=P/'run/A'/('archive-%04d'%n)
 if raw.exists():archive(raw,out,True)
raw=P/'run/A/checkpoint.pt'
if raw.exists():archive(raw,P/'run/A/archive',True)
last=P/'run/A/checkpoint-2966.pt'
if last.exists():assert sha(last)==read(P/'run/A/archive/checkpoint.json')['sha256'];last.unlink()
raw=P/'overfit/checkpoint.pt'
if raw.exists():archive(raw,P/'overfit/archive',True)
write(P/'NUMERICAL_POSTPROCESS.json',dict(complete=True,optimizer_updates=0,manual_semantic_review_still_required=True,checkpoint_count=len(list(P.rglob('archive*/checkpoint.json')))))
print('Numerical postprocess complete; do not infer language success without raw full-output review',flush=True)
