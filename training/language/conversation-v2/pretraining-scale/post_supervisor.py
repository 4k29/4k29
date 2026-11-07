"""Finite zero-update postprocess watcher, independent of chat connection."""
import fcntl,subprocess,sys,time,datetime,os
from common import *
lock=(P/'post.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);end=time.monotonic()+2400
while time.monotonic()<end:
 if(P/'NUMERICAL_POSTPROCESS.json').exists():break
 if read(P/'CONTINUATION_STATUS.json')['stage']=='FINITE_ONE_PASS_COMPLETE':
  write(P/'POST_STATUS.json',dict(supervisor=os.getpid(),stage='POSTPROCESS_RUNNING',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
  with(P/'postprocess.log').open('ab')as f:subprocess.run([sys.executable,str(P/'finish_numerical.py')],stdout=f,stderr=subprocess.STDOUT,check=True)
  break
 time.sleep(30)
else:raise RuntimeError('No completed training receipt within bounded watcher; no optimizer work started')
write(P/'POST_STATUS.json',dict(supervisor=os.getpid(),stage='NUMERICAL_POSTPROCESS_COMPLETE_MANUAL_REVIEW_PENDING',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
