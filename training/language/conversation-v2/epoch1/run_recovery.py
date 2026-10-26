"""One detached controller, medium then small, strict fixed first epoch only."""
import argparse,hashlib,json,os,pathlib,subprocess,sys,time
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[3]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main(a):
    if sha(a.amendment)!=a.amendment_sha:raise ValueError('Amendment hash changed')
    amendment=json.loads(a.amendment.read_text())
    for p,h in amendment['codeAndInputReceipts'].items():
        if sha(REPO/p)!=h:raise ValueError('Frozen recovery source changed')
    if not amendment['recoveryAuthorized']:raise ValueError('No recovery authorization')
    launches=HERE/'recovery-process-ledger.jsonl'
    if launches.exists():raise ValueError('Refuse duplicate detached controller')
    def event(row):
        with launches.open('a')as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
    event(dict(event='controller',pid=os.getpid(),ppid=os.getppid(),session=os.getsid(0),unix=time.time(),amendmentSha256=a.amendment_sha))
    for model in ['medium','small']:
        command=[sys.executable,str(HERE/'recover_train.py'),'--amendment',str(a.amendment),'--amendment-sha',a.amendment_sha,'--plan',str(HERE/'TRAIN_PLAN.json'),'--plan-sha',amendment['originalPlanSha256'],'--model',model,'--deadline',str(amendment['deadlineUnix'])]
        with (HERE/f'training-{model}-recovery.log').open('x')as log:
            process=subprocess.Popen(command,cwd=REPO,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
            event(dict(event='launch',model=model,pid=process.pid,ppid=os.getpid(),session=os.getsid(process.pid),unix=time.time(),command=command))
            print(json.dumps(dict(event='launch',model=model,pid=process.pid)),flush=True)
            code=process.wait()
        event(dict(event='exit',model=model,exitCode=code,unix=time.time()))
        if code!=0:raise RuntimeError(f'{model} failed; no automatic retry or next arm')
        receipt=json.loads((HERE/model/'receipt.json').read_text())
        if receipt['status']!='completed-first-train-epoch' or receipt['uniqueUpdates']!=3470 or receipt['actualContinuationUpdates']!=amendment['actualCaps'][model]:raise ValueError('First epoch incomplete; no automatic next training')
        print(json.dumps(dict(event='completed',model=model,checkpointSha256=receipt['checkpointSha256'],actualContinuationUpdates=receipt['actualContinuationUpdates'])),flush=True)
    event(dict(event='all-complete',actualContinuationUpdatesBoth=6012,automaticNextEpoch=False,unix=time.time()))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--amendment',type=pathlib.Path,required=True);p.add_argument('--amendment-sha',required=True);main(p.parse_args())
