"""Bounded exact continuation of the first shuffled TRAIN epoch; no adoption."""
import argparse, copy, hashlib, io, json, math, os, pathlib, resource, shutil, signal, sys, time
import torch
HERE=pathlib.Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
from core import REPO, sha, digest, exact, restore, trajectory, open_tokens, pack, causal_ce, clip_grad_accurate


def read(p):return json.loads(pathlib.Path(p).read_text())
def write(p,v):
    tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)


def load_chunks(manifest):
    manifest=pathlib.Path(manifest);m=read(manifest);b=io.BytesIO();h=hashlib.sha256()
    for row in m['chunks']:
        p=manifest.parent/row['path']
        if sha(p)!=row['sha256'] or p.stat().st_size!=row['bytes']:raise ValueError('Corrupt archive part')
        with p.open('rb') as f:
            for block in iter(lambda:f.read(1048576),b''):b.write(block);h.update(block)
    if b.tell()!=m['bytes'] or h.hexdigest()!=m['sha256']:raise ValueError('Corrupt concatenation')
    b.seek(0);v=torch.load(b,map_location='cpu',weights_only=False);b.close();return v


def save_chunks(payload,manifest):
    """Atomic manifest replacement, verified durable parts; retain previous until commit."""
    b=io.BytesIO();torch.save(payload,b);size=b.tell();b.seek(0)
    h=hashlib.sha256(b.getbuffer()).hexdigest();folder=manifest.parent/(manifest.stem+'.chunks.'+h[:12])
    folder.mkdir(exist_ok=False);rows=[]
    try:
        i=0
        while block:=b.read(40*1024*1024):
            p=folder/f'part-{i:03d}.bin'
            with p.open('wb') as f:f.write(block);f.flush();os.fsync(f.fileno())
            checksum=hashlib.sha256(block).hexdigest()
            if sha(p)!=checksum:raise AssertionError('Checkpoint write verification failed')
            rows.append(dict(path=str(p.relative_to(manifest.parent)),bytes=len(block),sha256=checksum));i+=1
        old=read(manifest) if manifest.exists() else None
        write(manifest,dict(schemaVersion=1,filename='checkpoint.pt',bytes=size,sha256=h,chunks=rows,losslessByteConcatenation=True))
        if old:
            for r in old['chunks']:(manifest.parent/r['path']).unlink()
            (manifest.parent/old['chunks'][0]['path']).parent.rmdir()
    except BaseException:
        # Incomplete newly written parts remain for diagnosis; prior manifest is untouched.
        raise
    finally:b.close()
    return h


def main(a):
    if sha(a.plan)!=a.plan_sha:raise ValueError('Plan SHA mismatch')
    plan=read(a.plan)
    if not a.preflight_only and plan.get('trainingAuthorized') is not True:raise ValueError('Training not authorized by frozen plan')
    for p,h in plan['codeReceipts'].items():
        if sha(REPO/p)!=h:raise ValueError('Frozen code changed: '+p)
    data=read(REPO/plan['dataPath'])
    if sha(REPO/plan['dataPath'])!=plan['dataSha256']:raise ValueError('Data manifest mismatch')
    if a.deadline>plan['globalDeadlineUnix']:raise ValueError('Global deadline extension')
    torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
    settings=read(BASE/'PLAN.json')['training'];values,windows=open_tokens(data,'train')
    out=HERE/a.model;out.mkdir(exist_ok=True)
    storage=pathlib.Path(plan['checkpointRoot'])/a.model;storage.mkdir(parents=True,exist_ok=True)
    manifest=storage/'checkpoint.pt.chunks.json';ledger=out/'optimizer-ledger.jsonl'
    if not a.resume and (manifest.exists() or ledger.exists()):raise ValueError('Refuse duplicate execution without explicit resume')
    source=BASE/'pilot'/a.model/'checkpoint.pt.chunks.json'
    if read(source)['sha256']!=plan['initialStates'][a.model]:raise ValueError('Wrong source checkpoint')
    saved=load_chunks(manifest if a.resume else source);state=saved['trajectory']
    if a.resume and (saved['planSha256']!=a.plan_sha or saved['deadline']!=a.deadline):raise ValueError('Resume plan/deadline mismatch')
    if (not a.resume and (state['uniqueUpdates']!=512 or state['cursor']!=2048)) or len(state['order'])!=13878:raise ValueError('Wrong first epoch position')
    if sorted(state['order'])!=list(range(len(windows))):raise ValueError('Not one full shuffled epoch')
    if any(float(s['step'])!=state['uniqueUpdates'] for s in state['optimizer']['state'].values()):raise ValueError('Adam counter mismatch')
    if any(g['lr']!=3e-5 for g in state['optimizer']['param_groups']):raise ValueError('Initial LR is not terminal LR')
    initial_digest=digest(state);model,opt,rng=restore(state,settings)
    if not exact(trajectory(model,opt,rng,state['order'],state['cursor'],state['history'],state['uniqueUpdates']),state):raise AssertionError('Initial restore mismatch')
    order=state['order'];cursor=state['cursor'];history=state['history'];unique=state['uniqueUpdates'];actual=saved['actualContinuationUpdates'] if a.resume else 0
    old_actual=514;start=time.time();resume_audit=saved['resumeAudit'] if a.resume else {'passed':False}
    if not a.resume and saved['actualOptimizerUpdates']!=514:raise ValueError('Wrong original actual counter')
    if a.resume:
        events=[json.loads(line)for line in ledger.read_text().splitlines()]
        if len(events)!=2*actual or sum(e['event']=='after-step'for e in events)!=actual:raise ValueError('Ledger/checkpoint gap: refuse uncounted replay')
    del saved,state
    before=digest(trajectory(model,opt,rng,order,cursor,history,unique));rng0=torch.get_rng_state().clone()
    indices=order[cursor:cursor+4];x,y,stats=pack(values,windows,indices,model.config['vocabulary'])
    opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);loss.backward()
    if any(p.grad is None or not bool(torch.isfinite(p.grad).all()) for p in model.parameters()):raise ValueError('Bad preflight gradient')
    norm=clip_grad_accurate(model.parameters(),1.);norm_after=sum(float(p.grad.double().square().sum())for p in model.parameters())**.5
    if norm_after>1+2e-5:raise AssertionError('Clipping bound')
    opt.zero_grad(set_to_none=True);torch.set_rng_state(rng0)
    if digest(trajectory(model,opt,rng,order,cursor,history,unique))!=before:raise AssertionError('Preflight altered state')
    pf=dict(initialTrajectoryDigest=initial_digest,exactRestore=True,scalarLoss=float(loss.detach()),gradientNorm=float(norm),clippedNorm=norm_after,finite=True,actualOptimizerUpdates=0,planSha256=a.plan_sha,originalCheckpointSha256=plan['initialStates'][a.model])
    pfpath=out/('preflight-v2.json' if a.preflight_only else 'run-zero-update-preflight.json')
    if pfpath.exists():raise ValueError('Refuse overwriting zero-update audit')
    write(pfpath,pf);del x,y,loss
    if a.preflight_only:return
    stopped={'signal':False}
    for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,lambda s,f:stopped.update(signal=True))
    def event(v):
        with ledger.open('a') as f:f.write(json.dumps(v)+'\n');f.flush();os.fsync(f.fileno())
    def payload(status):
        t=trajectory(model,opt,rng,order,cursor,history,unique)
        return dict(schemaVersion=1,scope='Isolated first-epoch continuation; not adopted',modelName=a.model,planSha256=a.plan_sha,initialCheckpointSha256=plan['initialStates'][a.model],dataSha256=plan['dataSha256'],tokenizerSha256=data['tokenizerSha256'],status=status,deadline=a.deadline,actualContinuationUpdates=actual,cumulativeActualOptimizerUpdates=old_actual+actual,resumeAudit=resume_audit,trajectory=t,config=t['config'],model=t['model'])
    def update(replay=False):
        nonlocal cursor,actual,unique
        if actual>=2960:raise ValueError('Actual continuation update cap')
        indices=order[cursor:min(cursor+4,len(order))]
        if not indices:raise ValueError('Cannot enter a second epoch')
        x,y,stats=pack(values,windows,indices,model.config['vocabulary']);opt.zero_grad(set_to_none=True)
        loss=causal_ce(model(x),y)
        if not bool(torch.isfinite(loss)):raise ValueError('Nonfinite loss')
        loss.backward()
        if any(p.grad is None or not bool(torch.isfinite(p.grad).all()) for p in model.parameters()):raise ValueError('Nonfinite gradient')
        norm=clip_grad_accurate(model.parameters(),1.)
        for g in opt.param_groups:g['lr']=3e-5
        event(dict(event='before-step',actualUpdate=actual+1,uniqueUpdate=unique+1,replay=replay))
        opt.step();actual+=1;cursor+=len(indices);unique+=1
        event(dict(event='after-step',actualUpdate=actual,uniqueUpdate=unique,replay=replay))
        if any(not bool(torch.isfinite(p).all()) for p in model.parameters()):raise ValueError('Nonfinite model')
        history.append(dict(uniqueUpdate=unique,windowIndices=indices,**stats,loss=float(loss.detach()),learningRate=3e-5,preclipGradientNorm=float(norm),clipped=bool(norm>1),torchRngDigest=digest(torch.get_rng_state()),samplerRngDigest=digest(rng.getstate())))
    try:
        status='running'
        if not a.resume:save_chunks(payload(status),manifest)
        while cursor<len(order):
            if stopped['signal'] or time.time()>=a.deadline:status='stopped-at-complete-update-resource-bound';break
            reserve=read(manifest)['bytes']+32*1024*1024
            if shutil.disk_usage(storage).free<reserve:status='stopped-at-complete-update-disk-bound';break
            update()
            if unique==514:
                save_chunks(payload('resume-audit-midpoint'),manifest)
            if unique==516 and not resume_audit['passed']:
                reference=trajectory(model,opt,rng,order,cursor,history,unique);mid=load_chunks(manifest)
                restored=mid['trajectory'];model,opt,rng=restore(restored,settings)
                order=restored['order'];cursor=restored['cursor'];history=restored['history'];unique=restored['uniqueUpdates']
                update(True);update(True)
                if not exact(trajectory(model,opt,rng,order,cursor,history,unique),reference):raise AssertionError('Disk-resume replay mismatch')
                resume_audit=dict(passed=True,allModelAdamRngSamplerHistoryBitwiseEqual=True,replayActualUpdates=2,midpointSha256=read(manifest)['sha256']);del reference,mid,restored
            if unique%128==0:
                save_chunks(payload('running'),manifest)
                print(json.dumps(dict(model=a.model,uniqueUpdates=unique,actualContinuationUpdates=actual,cursor=cursor,loss=history[-1]['loss'],elapsedSeconds=time.time()-start)),flush=True)
        if cursor==len(order):status='completed-first-train-epoch'
        checkpoint_sha=save_chunks(payload(status),manifest)
    except BaseException as error:
        events=[json.loads(line)for line in ledger.read_text().splitlines()] if ledger.exists() else []
        report=dict(error=repr(error),planSha256=a.plan_sha,knownCompletedActualContinuationUpdates=actual,
            retainedUniqueUpdateCounter=unique,automaticResumePermitted=False,
            ledgerHasUnmatchedBeforeStep=len(events)%2==1,
            authoritativeDurableCheckpoint=read(manifest) if manifest.exists() else None,
            partialOptimizerStepPossible=len(events)%2==1,forensicStateIsNotResumeCheckpoint=True)
        try:
            forensic=payload('FAILURE_FORENSIC_ONLY_NOT_RESUMABLE')
            forensic['failure']=report
            report['forensicStateSha256']=save_chunks(forensic,storage/'failure-state.pt.chunks.json')
        except BaseException as preservation_error:
            report['forensicPreservationError']=repr(preservation_error)
        write(out/'failure.json',report)
        raise
    counters=sorted({float(s['step'])for s in opt.state_dict()['state'].values()})
    if counters!=[float(unique)]:raise AssertionError('Wrong terminal Adam count')
    new=history[512:];used=[i for row in history for i in row['windowIndices']]
    if len(set(used))!=len(used) or used!=order[:cursor]:raise AssertionError('Epoch order duplicated/skipped')
    result=dict(status=status,modelName=a.model,uniqueUpdates=unique,retainedContinuationUpdates=unique-512,actualContinuationUpdates=actual,cumulativeActualOptimizerUpdates=old_actual+actual,replayOptimizerUpdates=actual-(unique-512),firstEpochWindows=len(order),windowsProcessed=cursor,firstEpochFraction=cursor/len(order),newTargetTokens=sum(r['targetTokens']for r in new),cumulativeTargetTokens=sum(r['targetTokens']for r in history),newBodyTokens=sum(r['targetTokens']-r['eosPositions']-r['rolePositions']for r in new),history=history,finalAdamCounters=counters,resumeAudit=resume_audit,checkpointSha256=checkpoint_sha,checkpointManifest=str(manifest),checkpointStorage='tmpfs; process-resumable, host memory loss requires archived Git chunks',planSha256=a.plan_sha,originalCheckpointSha256=plan['initialStates'][a.model],elapsedSeconds=time.time()-start,maximumRssKiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,adopted=False,sealedTestUsed=False)
    write(out/'receipt.json',result);print(json.dumps({k:v for k,v in result.items()if k!='history'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=pathlib.Path,required=True);p.add_argument('--plan-sha',required=True);p.add_argument('--model',choices=['small','medium'],required=True);p.add_argument('--deadline',type=float,required=True);p.add_argument('--preflight-only',action='store_true');p.add_argument('--resume',action='store_true');main(p.parse_args())
