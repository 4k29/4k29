"""Bounded durable supervisor. No extra budgets or conditional studies auto-authorized."""
import json,os,pathlib,subprocess,sys,time
N=pathlib.Path(__file__).resolve().parent

def identity(pid):
 try:
  s=pathlib.Path('/proc/'+str(pid)+'/stat').read_text();return dict(pid=pid,start_ticks=s[s.rindex(')')+2:].split()[19])
 except FileNotFoundError:return None

def status(stage,child=None):
 r=dict(supervisor=identity(os.getpid()),stage=stage,child=identity(child)if child else None,UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));p=N/'WORKFLOW_STATUS.json';q=p.with_suffix('.pending');q.write_text(json.dumps(r,indent=2)+'\n');os.replace(q,p)

def run(stage,script,*args):
 with(N/(stage+'.log')).open('a')as log:
  log.write('\nATTEMPT '+time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+'\n');log.flush();child=subprocess.Popen([sys.executable,str(N/script),*args],stdout=log,stderr=subprocess.STDOUT);status(stage,child.pid);code=child.wait()
  if code:status('FAILED '+stage+' exit='+str(code));raise SystemExit(code)

def main():
 status('started')
 for arm in ['control','boundary']:
  folder=N/'run'/arm
  if not(folder/'receipt.json').exists():run('training-'+arm,'train.py','--arm',arm,*(['--resume']if(folder/'updates.jsonl').exists()else[]))
  if not(folder/'archive/checkpoint.json').exists():run('archive-'+arm,'archive.py',arm)
 for arm in ['control','boundary']:
  for suffix,script in [('', 'evaluate.py'),('-human32','evaluate_qa.py'),('-paragraphs','evaluate_paragraphs.py'),('-RP','evaluate_rp.py')]:
   if not(N/'evaluation'/(arm+suffix+'.json')).exists():run('evaluation-'+arm+suffix,script,'--model',arm)
  if not(N/'forms'/(arm+'-native.json')).exists():run('ends-'+arm,'audit_new_forms.py','--models',arm)
  if not(N/'forms'/(arm+'-QA.json')).exists():run('forms-'+arm,'form_audit.py','--new',arm)
  if not(N/'diagnostic-new'/(arm+'.json')).exists():run('probabilities-'+arm,'diagnose_new.py','--models',arm)
 status('COMPLETE matched comparison; no automatic clip5 or expansion')
if __name__=='__main__':main()
