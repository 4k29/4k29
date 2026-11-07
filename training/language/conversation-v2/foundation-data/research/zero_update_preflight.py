"""Frozen CPU forward/backward audit. No optimizer update or model adoption.

Inputs must already be fixed TRAIN token windows. Model/Adam/RNG/history are
restored to their inherited state after every audit; no optimizer.step call exists.
"""
import argparse,hashlib,io,json,math,pathlib,resource,subprocess,sys,time
import torch
from torch.nn import functional as F
HERE=pathlib.Path(__file__).resolve().parent
BASE=HERE.parents[1]
REPO=HERE.parents[4]
sys.path.insert(0,str(BASE))
from core import digest,exact,restore,trajectory,causal_ce,clip_grad_accurate

def read(p):return json.loads(pathlib.Path(p).read_text())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def file_for(relative):
    p=(REPO/relative).resolve()
    if not p.is_relative_to(REPO):raise ValueError('Frozen code paths must remain in repository')
    return p

def load_checkpoint(manifest,expected):
    """Lossless RAM load, with committed-Git fallback for sparse workspace parts."""
    manifest=pathlib.Path(manifest);m=read(manifest)
    if m['sha256']!=expected:raise ValueError('Wrong initial own checkpoint')
    output=io.BytesIO();whole=hashlib.sha256()
    for row in m['chunks']:
        p=(manifest.parent/row['path']).resolve()
        if not p.is_relative_to(manifest.parent.resolve()):raise ValueError('Unsafe archive part path')
        process=None
        if p.is_file():source=p.open('rb')
        else:
            if not p.is_relative_to(REPO):raise ValueError('Absent part has no committed Git path')
            process=subprocess.Popen(['git','show','HEAD:'+str(p.relative_to(REPO))],cwd=REPO,stdout=subprocess.PIPE)
            source=process.stdout
        part=hashlib.sha256();size=0
        try:
            for b in iter(lambda:source.read(1048576),b''):
                output.write(b);part.update(b);whole.update(b);size+=len(b)
        finally:source.close()
        if process is not None and process.wait()!=0:raise ValueError('Cannot read committed checkpoint part')
        if size!=row['bytes'] or part.hexdigest()!=row['sha256']:raise ValueError('Checkpoint part mismatch')
    if output.tell()!=m['bytes'] or whole.hexdigest()!=expected:raise ValueError('Checkpoint concatenation mismatch')
    output.seek(0);result=torch.load(output,map_location='cpu',weights_only=False);output.close();return result

def pack_batch(windows,vocabulary):
    if len(windows)!=4:raise ValueError('Fixed audit batch requires four windows')
    sequences=[]
    for w in windows:
        if w['partition']!='train':raise ValueError('Only fixed TRAIN diagnostic inputs allowed')
        seq=w['tokens']
        if len(seq)!=257 or any(type(t)is not int or t in(0,5)or not 1<=t<vocabulary for t in seq):
            raise ValueError('Require257 real own-vocabulary tokens; no PAD/reserved role')
        if w['format']=='native-prose-bos-body-eos':
            start=w['documentTokenOffset'];end=start+len(seq);size=w['documentTokenCount']
            if start<0 or end>size:raise ValueError('Outside source article')
            if start==0 and seq[0]!=1:raise ValueError('True article start needs BOS')
            if end==size and seq[-1]!=2:raise ValueError('True article end needs EOS')
            if (1 in seq)and not(start==0 and seq[0]==1 and seq.count(1)==1):raise ValueError('Fake/mixed document BOS')
            if any(t in(3,4)for t in seq):raise ValueError('Prose must not invent human speaker roles')
            if 2 in seq and not(end==size and seq[-1]==2 and seq.count(2)==1):raise ValueError('Fake window EOS')
        sequences.append(seq)
    z=torch.tensor(sequences,dtype=torch.long);x=z[:,:-1].contiguous();y=z[:,1:].contiguous()
    body=int((y>=6).sum());eos=int((y==2).sum());roles=int(((y==3)|(y==4)).sum());other=int((y==1).sum())
    if body+eos+roles+other!=1024:raise AssertionError('All genuine target positions must count')
    return x,y,dict(targetTokens=1024,bodyTargets=body,eosTargets=eos,roleTargets=roles,otherSpecialTargets=other,paddingTargets=0)

def single_batch(model,opt,windows):
    x,y,dose=pack_batch(windows,model.config['vocabulary']);started=time.monotonic()
    opt.zero_grad(set_to_none=True);logits=model(x);loss=causal_ce(logits,y)
    if not bool(torch.isfinite(loss)):raise ValueError('Nonfinite audit CE')
    with torch.no_grad():
        nll=F.cross_entropy(logits.detach().reshape(-1,logits.shape[-1]),y.reshape(-1),reduction='none').reshape_as(y)
        nlls={name:float(nll[mask].mean())if bool(mask.any())else None for name,mask in
            [('body',y>=6),('eos',y==2),('role',(y==3)|(y==4))]}
    loss.backward()
    parameters=list(model.parameters())
    if any(p.grad is None or not bool(torch.isfinite(p.grad).all())for p in parameters):raise ValueError('Missing/nonfinite gradient')
    flat=torch.cat([p.grad.detach().reshape(-1).clone()for p in parameters])
    norm=float(clip_grad_accurate(parameters,1.))
    post=sum(float(p.grad.detach().double().square().sum())for p in parameters)**.5
    if not math.isfinite(norm)or post>1+2e-5:raise AssertionError('Gradient clipping integrity failed')
    mean=float(flat.double().mean());variance=float(flat.double().var(unbiased=False))
    result=dict(windowIds=[w['id']for w in windows],**dose,scalarCe=float(loss.detach()),nllByTargetKind=nlls,
        gradientNormFp64=norm,postclipNormFp64=post,clipped=norm>1.,clipCoefficient=min(1.,1./(norm+1e-6)),
        parameterGradientMean=mean,parameterGradientVariance=variance,maximumAbsoluteGradient=float(flat.abs().max()),
        finiteGradients=True,parameterTensors=len(parameters),parameters=sum(p.numel()for p in parameters),
        forwardBackwardSeconds=time.monotonic()-started,optimizerUpdates=0)
    opt.zero_grad(set_to_none=True);return result,flat

def run(a):
    if sha(a.plan)!=a.plan_sha256:raise ValueError('Frozen preflight plan SHA mismatch')
    plan=read(a.plan)
    if plan['optimizerUpdatesPermitted']!=0 or not plan['zeroUpdateAuditAuthorized']:raise ValueError('Only explicit zero-update audit authorized')
    for name,h in plan['codeReceipts'].items():
        if sha(file_for(name))!=h:raise ValueError('Frozen numerical source changed: '+name)
    inputs=file_for(plan['inputsPath'])
    if sha(inputs)!=plan['inputsSha256']:raise ValueError('Fixed TRAIN diagnostic inputs changed')
    bundle=read(inputs)
    if bundle['tokenizerSha256']!=plan['tokenizerSha256']:raise ValueError('Own tokenizer identity mismatch')
    if sha(file_for(plan['tokenizerPath']))!=plan['tokenizerSha256']:raise ValueError('Own vocabulary changed')
    if bundle['actualOptimizerUpdates']!=0:raise ValueError('Diagnostic bundle must not claim training')
    if a.output.exists():raise ValueError('Refuse zero-update audit output overwrite')
    checkpoint=file_for(plan['checkpointManifestPath']);manifest_before=sha(checkpoint)
    if manifest_before!=plan['checkpointManifestSha256']:raise ValueError('Initial archive manifest changed')
    torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
    saved=load_checkpoint(checkpoint,plan['checkpointSha256']);state=saved['trajectory']
    if state['uniqueUpdates']!=3470 or saved['modelName']!='medium':raise ValueError('Wrong frozen endpoint')
    settings=read(BASE/'PLAN.json')['training'];model,opt,rng=restore(state,settings)
    if not exact(trajectory(model,opt,rng,state['order'],state['cursor'],state['history'],3470),state):raise AssertionError('Inherited model/Adam/RNG/sampler/history restore differs')
    moments=opt.state_dict()['state']
    if len(moments)!=100 or any(float(s['step'])!=3470 for s in moments.values()):raise ValueError('Wrong inherited Adam counter')
    if any(not bool(torch.isfinite(s[k]).all())for s in moments.values()for k in ['exp_avg','exp_avg_sq']):raise ValueError('Nonfinite Adam moment')
    if any(not bool((s['exp_avg_sq']>=0).all())for s in moments.values()):raise ValueError('Negative second moment')
    guard={'attempts':0}
    def forbidden(*args,**kwargs):
        guard['attempts']+=1;raise AssertionError('optimizer updates are forbidden in this audit')
    opt.step=forbidden
    before=digest(trajectory(model,opt,rng,state['order'],state['cursor'],state['history'],3470))
    original_rng=torch.get_rng_state().clone();reports={'control':[],'dataadd':[]};pairs=[];next_rng=original_rng.clone()
    if set(bundle['conditions'])!={'control','dataadd'}or any(len(v)!=2 for v in bundle['conditions'].values()):raise ValueError('Exactly two paired batches per condition required')
    try:
        for i in range(2):
            condition_rng=next_rng.clone();torch.set_rng_state(condition_rng)
            c,gv=single_batch(model,opt,bundle['conditions']['control'][i]);after_control=torch.get_rng_state().clone()
            torch.set_rng_state(condition_rng);d,dv=single_batch(model,opt,bundle['conditions']['dataadd'][i]);after_dataadd=torch.get_rng_state().clone()
            if not torch.equal(after_control,after_dataadd):raise AssertionError('Paired dropout RNG consumption differs')
            if bundle['conditions']['control'][i][:2]!=bundle['conditions']['dataadd'][i][:2]:raise AssertionError('Common RP half-batch changed')
            norm_c=float(gv.double().norm());norm_d=float(dv.double().norm())
            cosine=float(torch.dot(gv.double(),dv.double())/(norm_c*norm_d))if norm_c and norm_d else None
            pairs.append(dict(batch=i,sameDropoutRngConsumption=True,commonRpWindowsIdentical=True,
                allTargetDoseEqual=c['targetTokens']==d['targetTokens'],bodyDoseEqual=c['bodyTargets']==d['bodyTargets'],
                gradientNormRatioDataaddToControl=norm_d/norm_c if norm_c else None,gradientCosine=cosine,
                noClaimBodyAndEosRoleDoseMatched=True))
            reports['control'].append(c);reports['dataadd'].append(d);next_rng=after_control
            del gv,dv
    finally:
        opt.zero_grad(set_to_none=True);torch.set_rng_state(original_rng)
    after=digest(trajectory(model,opt,rng,state['order'],state['cursor'],state['history'],3470))
    if before!=after or sha(checkpoint)!=manifest_before or guard['attempts']!=0:raise AssertionError('Audit altered state or attempted optimizer update')
    result=dict(status='PASS_ZERO_UPDATE_NUMERICAL_INTEGRITY_ONLY',planSha256=a.plan_sha256,
        checkpointSha256=plan['checkpointSha256'],inputsSha256=plan['inputsSha256'],modelName='medium',
        inheritedAdamCounters=[3470],inheritedAdamStateCount=100,inheritedMomentsFiniteAndNonnegative=True,
        exactInitialTrajectoryRestore=True,beforeTrajectoryDigest=before,afterTrajectoryDigest=after,
        modelAdamTorchPrivateRngSamplerOrderHistoryUnchanged=True,sourceCheckpointManifestUnchanged=True,
        actualOptimizerUpdates=0,optimizerStepAttempts=guard['attempts'],forwardBackwardBatches=4,
        conditions=reports,pairedComparisons=pairs,maximumProcessRssKiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        precision='FP32 parameters/Adam/gradients; original FP64 global norm clip max1 epsilon1e-6',
        threads=2,cuda=False,modelTrainingMode=model.training,sealedTestRead=False,
        learningGo=False,limitations=['Four TRAIN batches do not establish training convergence, generalization or response quality',
            'No optimizer update: complete checkpoint resume after a new update was not tested',
            'Source admission, full data/evaluation plan and durable resources remain separate gates',
            'Body/EOS/role dose changes with source representation; only all-target shape/dose matched'])
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ['conditions']},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=pathlib.Path,required=True);p.add_argument('--plan-sha256',required=True);p.add_argument('--output',type=pathlib.Path,required=True);run(p.parse_args())
