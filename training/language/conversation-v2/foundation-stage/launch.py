"""Single-worker supervisor, including orphan detection after supervisor death."""
import argparse,fcntl,json,os,pathlib,signal,subprocess,sys
H=pathlib.Path(__file__).resolve().parent
def identity(pid):
 try:
  text=pathlib.Path('/proc/'+str(pid)+'/stat').read_text();tail=text[text.rindex(')')+2:].split();return dict(pid=pid,start_ticks=tail[19])
 except FileNotFoundError:return None
def live_worker():
 p=H/'run/PROCESS.json'
 if not p.exists():return False
 r=json.loads(p.read_text());return identity(r['pid'])==r
def main():
 p=argparse.ArgumentParser();p.add_argument('--resume',action='store_true');p.add_argument('--mixed',action='store_true');a=p.parse_args();folder=H/'run';folder.mkdir(exist_ok=True)
 with(folder/'worker.lock').open('a')as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('Supervisor already running; no additional updates')
  if live_worker():raise SystemExit('Live worker detected; refusing second run')
  command=[sys.executable,str(H/('train_mixed.py'if a.mixed else'train.py'))]+(['--resume']if a.resume else[]);worker=subprocess.Popen(command)
  (folder/'PROCESS.json').write_text(json.dumps(identity(worker.pid),indent=2)+'\n')
  for s in [signal.SIGTERM,signal.SIGINT]:signal.signal(s,lambda sig,frame:worker.send_signal(sig))
  raise SystemExit(worker.wait())
if __name__=='__main__':main()
