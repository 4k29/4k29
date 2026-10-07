"""Complete raw learning and freeze both snapshots before any fresh TEST."""
import gzip,hashlib,json,pathlib,subprocess,sys,time
import torch
ROOT=pathlib.Path(__file__).resolve().parent;REPO=ROOT.parents[2]
from main_train import export_model
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def run(args,log):
    with log.open('w') as f:subprocess.run(args,cwd=REPO,stdout=f,stderr=subprocess.STDOUT,check=True)
def main():
    while not (ROOT/'pilot-8192/result.json').exists():time.sleep(10)
    runs=[]
    for merges in [4096,8192]:
        directory=ROOT/f'pilot-{merges}';r=read(directory/'result.json');m=read(directory/'metrics.json')
        assert r['completedRun'] and r['completedSteps']==1000
        assert r['trainerSourceSha256']==sha(ROOT/'train.py')
        runs.append(dict(merges=merges,completedUpdates=1000,parameters=r['parameters'],bestStep=r['bestStep'],validationNllPerUtf8Byte=m['bestValidationNllPerByte'],resultSha256=sha(directory/'result.json')))
    chosen=min(runs,key=lambda r:r['validationNllPerUtf8Byte'])['merges']
    write(ROOT/'vocabulary-choice.json',dict(chosenMerges=chosen,runs=runs,testUsed=False,selection='Lowest canonical raw-chain VAL byte NLL after same1000 updates; parameters and byte exposure differ'))
    directory=ROOT/'raw-chains-10000';directory.mkdir(exist_ok=True)
    if not (directory/'result.json').exists():
        command=[sys.executable,str(ROOT/'main_train.py'),'--merges',str(chosen),'--steps','10000','--dim','192','--layers','8','--heads','4','--batch','8','--threads','2','--seed','1429','--validation-every','1000','--run',directory.name,'--compile','--precision','bfloat16']
        if (directory/'checkpoint.pt').exists():command.append('--resume')
        run(command,directory/'training.log')
    from evaluate_validation import main as development_only
    development_only()
    print(json.dumps(dict(developmentOnly=True,testStillUnopened=True,manualLanguageReviewRequired=True)),flush=True)
if __name__=='__main__':main()
