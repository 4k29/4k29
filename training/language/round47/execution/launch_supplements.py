"""Detached read-only waiters. Never assign semantic scores or train."""
import pathlib,subprocess,json,sys,datetime
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';repo=R.parents[2];receipts=[]
assert not(E/'supplement-waiter-processes.json').exists()
for script,log in [(E/'audit_retained_control.py','paired-milestone-audit.log'),(E/'wait_interim.py','interim-waiter.log'),(E/'pack_retained_milestones.py','milestone-pack-waiter.log'),(R/'fixed-source-mrmp-dev/after_final.py','source-waiter.log'),(E/'wait_terminal_diagnostic.py','terminal-waiter.log'),(E/'wait_human_train_gap.py','train-gap-waiter.log'),(E/'wait_final_context.py','context-final-waiter.log')]:
 with(E/log).open('ab',buffering=0)as f:p=subprocess.Popen([sys.executable,str(script)],cwd=repo,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 receipts.append(dict(script=str(script.relative_to(R)),pid=p.pid,log=log))
(E/'supplement-waiter-processes.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),processes=receipts,noAdditionalOptimizerUpdates=True),indent=2)+'\n');print('Started read-only supplemental waiters')
