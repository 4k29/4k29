"""Single bounded two-width launch; no automatic follow-on experiments."""
import hashlib,json,pathlib,subprocess,sys,time
H=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=H/'PLAN.json';p=json.loads(plan.read_text());receipt=H/'pilot-launch.json'
    if receipt.exists():raise ValueError('This launch budget has already been used; do not repeat')
    assert p['trainingAuthorized'] is True
    start=time.time();deadline=start+p['allowedWallSeconds']
    r={'planSha256':sha(plan),'startedUnix':start,'absoluteSharedDeadlineUnix':deadline,
       'maximumActualUpdatesTotal':1028,'maximumActualPerArm':514,'newTaskBudgetDistinctFromPrior64Pair400':True,
       'commands':[],'status':'running'}
    def save():receipt.write_text(json.dumps(r,indent=2)+'\n')
    save()
    for name in ['small','medium']:
        command=[sys.executable,str(H/'train.py'),'--plan',str(plan),'--plan-sha256',sha(plan),'--model',name,'--deadline',str(deadline)]
        r['commands'].append(command);save()
        with (H/('training-'+name+'.log')).open('w')as f:
            result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
        r.setdefault('returnCodes',{})[name]=result.returncode;save()
        if result.returncode:
            r['status']='stopped-error-no-condition-retry';save();raise SystemExit(result.returncode)
    r['status']='finished-bounded-launch';r['elapsedSeconds']=time.time()-start
    rs={name:json.loads((H/'pilot'/name/'receipt.json').read_text())for name in ['small','medium']}
    r['actualOptimizerUpdates']=sum(s['actualOptimizerUpdates']for s in rs.values())
    r['retainedUniqueUpdates']={name:s['uniqueUpdates']for name,s in rs.items()}
    common=[n for n in [256,512]if all(s['uniqueUpdates']>=n for s in rs.values())]
    r['fixedCommonEvaluationMilestone']=max(common)if common else None
    assert r['actualOptimizerUpdates']<=1028
    save();print(json.dumps(r))
if __name__=='__main__':main()
