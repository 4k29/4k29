"""Bounded fresh-model pilot. No adoption, TEST access, or public-code changes."""
import argparse
import copy
import json
import os
import pathlib
import resource
import signal
import sys
import time

import torch

from core import (REPO, HERE, causal_ce, clip_grad_accurate, decoder, digest, exact, initialize, learning_rate,
                  next_batch, open_tokens, pack, restore, sha, trajectory)


def read(path): return json.loads(pathlib.Path(path).read_text())
def write(path, value):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def validate(plan_path, plan_sha, name):
    if sha(plan_path) != plan_sha: raise ValueError('Preregistered plan SHA mismatch')
    plan = read(plan_path)
    for path, expected in plan['codeReceipts'].items():
        candidate = (REPO/path).resolve()
        if not candidate.is_relative_to(REPO) or sha(candidate) != expected:
            raise ValueError('Frozen source mismatch: '+path)
    data_path = (REPO/plan['dataPath']).resolve()
    if sha(data_path) != plan['dataSha256']: raise ValueError('Frozen data manifest mismatch')
    data = read(data_path)
    tokenizer_path = (REPO/data['tokenizerPath']).resolve()
    if sha(tokenizer_path) != data['tokenizerSha256']: raise ValueError('Frozen tokenizer mismatch')
    tokenizer = read(tokenizer_path)
    config = copy.deepcopy(plan['models'][name])
    if config['vocabulary'] != len(tokenizer['bytes']): raise ValueError('Wrong own vocabulary')
    if config['layers'] != 8 or config['dim'] != {'small':192,'medium':320}[name] or config['context'] != 256:
        raise ValueError('Unregistered pilot architecture')
    if config['heads'] != 4 or config['hidden'] != 4*config['dim'] or config['dropout'] != .1:
        raise ValueError('Pilot must change width only')
    settings = plan['training']
    for k, v in dict(uniqueUpdates=512,batch=4,seed=2062,samplerSeed=2063,warmup=64,lr=3e-4,minLr=3e-5,weightDecay=.05).items():
        if settings[k] != v: raise ValueError('Unregistered training setting: '+k)
    return plan, data, tokenizer, config, settings


def preflight(model, optimizer, rng, values, windows, settings):
    before = digest(dict(model=model.state_dict(),optimizer=optimizer.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate()))
    torch_before = torch.get_rng_state().clone()
    private = type(rng)(); private.setstate(rng.getstate())
    indices, _, _ = next_batch(private, [], 0, len(windows), settings['batch'])
    x, y, stats = pack(values, windows, indices, model.config['vocabulary'])
    times = []
    try:
        for _ in range(2):
            started = time.monotonic(); optimizer.zero_grad(set_to_none=True)
            loss = causal_ce(model(x), y)
            if not bool(torch.isfinite(loss)): raise ValueError('Nonfinite preflight loss')
            loss.backward()
            gradients = [p.grad for p in model.parameters()]
            if any(g is None or not bool(torch.isfinite(g).all()) for g in gradients):
                raise ValueError('Missing or nonfinite gradient')
            # FP64 sum is an audit reference, not a change in FP32 training.
            squares = sum(float(g.detach().double().square().sum()) for g in gradients)
            norm64 = squares**.5
            clip = clip_grad_accurate(model.parameters(), 1.)
            if abs(float(clip)-norm64) > 2e-5+2e-5*abs(norm64):
                raise AssertionError('Gradient norm disagreement with FP64 reference')
            clipped_norm64=sum(float(g.detach().double().square().sum())for g in gradients)**.5
            if clipped_norm64>1.+2e-5:raise AssertionError('Clipped gradient exceeds fixed maximum')
            times.append(time.monotonic()-started)
        report = dict(**stats,scalarLoss=float(loss.detach()),gradientNormFp64=norm64,clippingNormFp64=float(clip),
            actualClippedNormFp64=clipped_norm64,maxGradientNorm=1.,
            clippingImplementation='FP64 global-L2 norm, common FP32 coefficient; max1 epsilon1e-6',
            finiteGradients=True,parameterTensors=len(gradients),parameters=sum(p.numel()for p in model.parameters()),
            secondsForwardBackward=times,secondBatchSeconds=times[-1],maximumRssKiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            actualOptimizerUpdates=0,indices=indices)
    finally:
        optimizer.zero_grad(set_to_none=True); torch.set_rng_state(torch_before)
    after = digest(dict(model=model.state_dict(),optimizer=optimizer.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate()))
    if before != after: raise AssertionError('Zero-update audit changed model/Adam/RNG')
    report['modelOptimizerRngUnchanged'] = True
    return report


def run(a):
    plan, data, tokenizer, config, settings = validate(a.plan, a.plan_sha256, a.model)
    if not a.preflight_only and plan.get('trainingAuthorized') is not True:
        raise ValueError('This plan does not authorize training')
    torch.set_num_threads(settings['threads']); torch.use_deterministic_algorithms(True)
    values, windows = open_tokens(data, 'train')
    output = HERE/'pilot'/a.model; output.mkdir(parents=True, exist_ok=True)
    if a.preflight_only:
        path = output/'preflight.json'
        if path.exists(): raise ValueError('Refuse to overwrite preflight receipt')
        model, optimizer, rng = initialize(config, settings)
        result = preflight(model,optimizer,rng,values,windows,settings)
        result.update(planSha256=a.plan_sha256,dataSha256=plan['dataSha256'],tokenizerSha256=data['tokenizerSha256'],config=config,
            torchVersion=torch.__version__,threads=torch.get_num_threads(),cuda=False,precision='FP32')
        write(path,result); print(json.dumps(result)); return
    if a.deadline is None: raise ValueError('Training requires an explicit absolute wall-clock deadline')
    if a.deadline-time.time() > plan.get('allowedWallSeconds',1800)+1:
        raise ValueError('Requested deadline exceeds preregistered resource ceiling')
    checkpoint = output/'checkpoint.pt'; ledger = output/'optimizer-ledger.jsonl'; mid = output/'resume-step2.pt'
    if a.resume:
        saved = torch.load(checkpoint,map_location='cpu',weights_only=False)
        if saved['planSha256'] != a.plan_sha256 or saved['modelName'] != a.model:
            raise ValueError('Resume plan/model mismatch')
        if saved['deadline'] != a.deadline: raise ValueError('Refuse implicit wall-budget extension')
        state=saved['trajectory']; model,optimizer,rng=restore(state,settings)
        order=state['order'];cursor=state['cursor'];history=state['history'];unique=state['uniqueUpdates']
        actual=saved['actualOptimizerUpdates'];resume_audit=saved['resumeAudit'];started=saved['startedUnix']
        events=[json.loads(line)for line in ledger.read_text().splitlines()]
        if len([x for x in events if x['event']=='after-step']) != actual or len(events)!=2*actual:
            raise ValueError('Ledger exceeds durable checkpoint; refuse uncounted replay')
    else:
        if checkpoint.exists() or ledger.exists(): raise ValueError('Refuse duplicate training execution')
        model,optimizer,rng=initialize(config,settings)
        order=[];cursor=0;history=[];unique=0;actual=0;resume_audit={'passed':False};started=time.time()
    stopped = {'signal':False}
    def stop_signal(signum, frame): stopped['signal']=True
    for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,stop_signal)
    def emit(row):
        with ledger.open('a')as f:
            f.write(json.dumps(row,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def save(status):
        payload=dict(schemaVersion=1,scope='Fresh conversation-v2 pilot; not adopted',modelName=a.model,
            planSha256=a.plan_sha256,dataSha256=plan['dataSha256'],tokenizerSha256=data['tokenizerSha256'],
            actualOptimizerUpdates=actual,resumeAudit=resume_audit,startedUnix=started,deadline=a.deadline,status=status,
            trajectory=trajectory(model,optimizer,rng,order,cursor,history,unique))
        # Evaluation-compatible aliases refer to the same tensor storage; the
        # complete training trajectory remains the authoritative resume state.
        payload['config']=payload['trajectory']['config'];payload['model']=payload['trajectory']['model']
        temp=checkpoint.with_suffix('.tmp');torch.save(payload,temp);temp.replace(checkpoint)
    def update(step,replay=False):
        nonlocal order,cursor,actual
        if actual >= settings['uniqueUpdates']+2: raise ValueError('Hard actual-update budget exhausted')
        indices,order,cursor=next_batch(rng,order,cursor,len(windows),settings['batch'])
        x,y,stats=pack(values,windows,indices,config['vocabulary'])
        lr=learning_rate(step,settings)
        for group in optimizer.param_groups:group['lr']=lr
        optimizer.zero_grad(set_to_none=True);loss=causal_ce(model(x),y)
        if not bool(torch.isfinite(loss)):raise ValueError('Nonfinite loss before optimizer step')
        loss.backward()
        if any(p.grad is None or not bool(torch.isfinite(p.grad).all())for p in model.parameters()):
            raise ValueError('Missing/nonfinite gradient before optimizer step')
        norm=clip_grad_accurate(model.parameters(),1.)
        emit(dict(event='before-step',actualUpdate=actual+1,uniqueUpdate=step,replay=replay))
        optimizer.step();actual+=1
        emit(dict(event='after-step',actualUpdate=actual,uniqueUpdate=step,replay=replay))
        if any(not bool(torch.isfinite(p).all())for p in model.parameters()):raise ValueError('Nonfinite updated model')
        return dict(uniqueUpdate=step,windowIndices=indices,**stats,loss=float(loss.detach()),learningRate=lr,
            preclipGradientNorm=float(norm),clipped=bool(norm>1),torchRngDigest=digest(torch.get_rng_state()),
            samplerRngDigest=digest(rng.getstate()))
    status='running'
    if not a.resume:save('initialized-zero-updates')
    try:
        while unique < settings['uniqueUpdates']:
            if stopped['signal'] or time.time() >= a.deadline:
                status='stopped-at-complete-update-resource-bound';break
            step=unique+1;history.append(update(step));unique=step
            if unique==2:
                temp=mid.with_suffix('.tmp');torch.save(trajectory(model,optimizer,rng,order,cursor,history,unique),temp);temp.replace(mid)
            if unique==4 and not resume_audit['passed']:
                reference=trajectory(model,optimizer,rng,order,cursor,history,unique)
                loaded=torch.load(mid,map_location='cpu',weights_only=False);mid_sha=sha(mid)
                del model,optimizer,rng
                model,optimizer,rng=restore(loaded,settings)
                order=loaded['order'];cursor=loaded['cursor'];history=loaded['history']
                if not exact(trajectory(model,optimizer,rng,order,cursor,history,2),loaded):raise AssertionError('Disk reload differs')
                history.extend([update(3,True),update(4,True)])
                if not exact(trajectory(model,optimizer,rng,order,cursor,history,4),reference):raise AssertionError('Resume trajectory differs')
                resume_audit=dict(passed=True,replayActualUpdates=2,allModelOptimizerRngSamplerAndTraceBitwiseEqual=True,
                                  midpointSha256=mid_sha)
                mid.unlink();del reference,loaded
            if unique%32==0:
                save('running'); print(json.dumps(dict(model=a.model,uniqueUpdates=unique,actualUpdates=actual,loss=history[-1]['loss'])),flush=True)
                if unique==256:
                    milestone=output/'weights-256.pt'
                    if milestone.exists():raise ValueError('Refuse milestone overwrite')
                    temporary=milestone.with_suffix('.tmp')
                    torch.save(dict(config=config,model=model.state_dict(),modelName=a.model,uniqueUpdates=unique,
                        actualOptimizerUpdates=actual,planSha256=a.plan_sha256,dataSha256=plan['dataSha256'],
                        tokenizerSha256=data['tokenizerSha256'],torchRngDigest=digest(torch.get_rng_state()),
                        samplerRngDigest=digest(rng.getstate()),scope='Fixed resource milestone; no loss selection'),temporary)
                    temporary.replace(milestone)
        if unique==settings['uniqueUpdates']:status='completed-fixed-terminal'
        save(status)
    except BaseException as error:
        # A before/after-ledger gap is intentionally not auto-replayed. It may
        # indicate a partially interrupted update and must be manually audited.
        failure=dict(error=repr(error),uniqueUpdates=unique,actualOptimizerUpdates=actual,
              planSha256=a.plan_sha256,automaticResumePermitted=False)
        # Preserve inspectable current state without pretending a possibly
        # interrupted optimizer.step is a completed, resumable update.
        try:
            events=[json.loads(line)for line in ledger.read_text().splitlines()]if ledger.exists()else[]
            failure['unmatchedBeforeStep']=len(events)%2==1
            failure['forensicStateIsNotAResumeCheckpoint']=True
            forensic=dict(config=config,model=model.state_dict(),optimizer=optimizer.state_dict(),
                torchRng=torch.get_rng_state(),pythonRng=rng.getstate(),order=order,cursor=cursor,
                history=history,**failure)
            temporary=output/'failure-state.tmp';torch.save(forensic,temporary)
            temporary.replace(output/'failure-state.pt')
            failure['forensicStateSha256']=sha(output/'failure-state.pt')
        except BaseException as preservation_error:
            failure['forensicPreservationError']=repr(preservation_error)
        write(output/'failure.json',failure)
        raise
    counters=sorted({float(s['step'])for s in optimizer.state_dict()['state'].values()})
    result=dict(status=status,modelName=a.model,config=config,parameters=sum(p.numel()for p in model.parameters()),
        actualOptimizerUpdates=actual,uniqueUpdates=unique,replayOptimizerUpdates=actual-unique,finalAdamCounters=counters,
        resumeAudit=resume_audit,history=history,checkpointSha256=sha(checkpoint),
        planSha256=a.plan_sha256,dataSha256=plan['dataSha256'],tokenizerSha256=data['tokenizerSha256'],
        maximumRssKiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,elapsedSeconds=time.time()-started,
        generationUsedForSelection=False,adopted=False,externalWeights=False,sealedTestUsed=False)
    write(output/'receipt.json',result)
    print(json.dumps({k:v for k,v in result.items()if k!='history'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=pathlib.Path,required=True);p.add_argument('--plan-sha256',required=True)
    p.add_argument('--model',choices=['small','medium'],required=True);p.add_argument('--preflight-only',action='store_true')
    p.add_argument('--resume',action='store_true');p.add_argument('--deadline',type=float)
    run(p.parse_args())
