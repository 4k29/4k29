"""Disposable paired ordinary-response-CE assay. Never an adoption trainer.

Each arm has 198 unique updates plus two actual replay updates: 200 total.
Each arm's append-only ledger counts optimizer.step calls, including replays.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import pathlib
import random

import torch
from torch.nn import functional as F

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
CHECKPOINT = REPO / 'training/language/round46/continue-10000/best-aligned-checkpoint.pt'
CHECKPOINT_SHA = 'd99f85f706d40702393410c05733274bcc59528c7c776ff9ba3cea74d2647f1d'


def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    h = hashlib.sha256()
    def visit(x):
        if isinstance(x, torch.Tensor):
            t = x.detach().cpu().contiguous()
            h.update(str((str(t.dtype), tuple(t.shape))).encode()); h.update(t.numpy().tobytes())
        elif isinstance(x, dict):
            for k in sorted(x, key=str):
                h.update(repr(k).encode()); visit(x[k])
        elif isinstance(x, (list, tuple)):
            h.update(type(x).__name__.encode())
            for y in x: visit(y)
        else: h.update(repr(x).encode())
    visit(value)
    return h.hexdigest()


def exact(a, b):
    if type(a) is not type(b): return False
    if isinstance(a, torch.Tensor): return a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b)
    if isinstance(a, dict): return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)): return len(a) == len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a == b


def load_initial():
    if sha(CHECKPOINT) != CHECKPOINT_SHA: raise ValueError('Initial checkpoint SHA mismatch')
    saved = torch.load(CHECKPOINT, map_location='cpu', weights_only=False)
    if saved['step'] != 9500 or any(float(v['step']) != 29500 for v in saved['optimizer']['state'].values()):
        raise ValueError('Wrong selected model or Adam age')
    if not exact(saved['model'], saved['beststate']): raise ValueError('Selected weights not aligned')
    spec = importlib.util.spec_from_file_location('_learnability_own_model', REPO/'training/language/model.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    model = module.Decoder(saved['config']); model.load_state_dict(saved['model'])
    optimizer = torch.optim.AdamW(model.parameters(), lr=4.5e-5, weight_decay=.05)
    optimizer.load_state_dict(copy.deepcopy(saved['optimizer']))
    if any(g['lr'] != 4.4999999999999996e-5 for g in optimizer.param_groups): raise ValueError('Wrong inherited LR')
    rng = random.Random(); rng.setstate(saved['pythonRng']); torch.set_rng_state(saved['torchRng'])
    model.eval()
    if not exact(model.state_dict(),saved['model']) or not exact(optimizer.state_dict(),saved['optimizer']):
        raise AssertionError('Initial state restoration failed')
    return model, optimizer, rng


def response_ce(model, rows, arm):
    """Existing context_preference.py CE: no EOS, per-example mean, eval mode."""
    was_training = model.training
    try:
        with torch.random.fork_rng(devices=[]):
            model.eval(); examples = []
            for row in rows:
                prefix = row['prefixTokens'] if arm == 'A' else row['wrongPrefixTokens']
                target = row['targetTokens']; seq = prefix + target
                if prefix[0] != 1 or len(seq)-1 > model.config['context']: raise ValueError('Invalid sequence')
                examples.append((seq,len(prefix),len(target)))
            width = max(len(s)-1 for s,_,_ in examples)
            x = torch.zeros((len(rows),width),dtype=torch.long); y = torch.full_like(x,-100)
            for i,(seq,start,n) in enumerate(examples):
                x[i,:len(seq)-1] = torch.tensor(seq[:-1]); y[i,start-1:start-1+n] = torch.tensor(seq[start:])
            logits = model(x)
            raw = F.cross_entropy(logits.reshape(-1,model.config['vocabulary']),y.reshape(-1),reduction='none').reshape_as(y)
            means = raw.sum(-1)/y.ne(-100).sum(-1)
            # Independent direct-position reduction verifies masks and normalization.
            independent = torch.stack([F.cross_entropy(logits[i,start-1:start-1+n],torch.tensor(seq[start:]))
                for i,(seq,start,n) in enumerate(examples)]).mean()
            loss = means.mean()
            if not torch.allclose(loss,independent,atol=2e-6,rtol=2e-6): raise AssertionError('CE normalization differs')
            return loss, dict(targetTokens=int(y.ne(-100).sum()),exampleNll=[float(v) for v in means.detach()])
    finally: model.train(was_training)


def snapshot(model,optimizer,rng,order,cursor,history,unique):
    return copy.deepcopy(dict(config=model.config,model=model.state_dict(),optimizer=optimizer.state_dict(),
        torchRng=torch.get_rng_state(),pythonRng=rng.getstate(),order=order,cursor=cursor,
        history=history,uniqueUpdates=unique,modelTraining=model.training))


def first_batch_preflight(model,opt,rng,rows,arm):
    before=digest(dict(model=model.state_dict(),optimizer=opt.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate()))
    private=random.Random(); private.setstate(rng.getstate()); order=list(range(64)); private.shuffle(order)
    opt.zero_grad(set_to_none=True)
    loss,record=response_ce(model,[rows[i] for i in order[:8]],arm)
    if not bool(torch.isfinite(loss)): raise ValueError('Nonfinite preflight CE')
    loss.backward(); grads=[p.grad for p in model.parameters()]
    if any(g is None or not bool(torch.isfinite(g).all()) for g in grads): raise ValueError('Invalid preflight gradients')
    flat=torch.cat([g.detach().reshape(-1) for g in grads])
    norm=torch.linalg.vector_norm(flat)
    clipped=torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
    record.update(loss=float(loss.detach()),preclipGradientNorm=float(norm),clipped=bool(norm>1),
        gradientElementVariance=float(flat.double().var(unbiased=False)),gradientMaxAbs=float(flat.abs().max()),
        parameterGradientTensors=len(grads),optimizerUpdates=0)
    if not torch.allclose(norm,clipped,atol=2e-5,rtol=2e-5): raise AssertionError('Gradient norm disagreement')
    opt.zero_grad(set_to_none=True)
    # Independently execute the immutable original R46 implementation, including
    # its unused wrong-context forward rows, to verify the intended CE exactly.
    source=REPO/'training/language/round46/context_preference.py'
    spec=importlib.util.spec_from_file_location('_learnability_original_response_ce',source)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    pool=[]
    for i in order[:8]:
        r=rows[i]; positive=r['prefixTokens'] if arm=='A' else r['wrongPrefixTokens']
        negative=r['wrongPrefixTokens'] if arm=='A' else r['prefixTokens']
        pool.append(dict(prefixTokens=positive[1:],wrongPrefixTokens=negative[1:],targetTokens=r['targetTokens']))
    reference,_=module.preference_loss(model,pool,0,batch=8)
    reference.backward(); reference_flat=torch.cat([p.grad.detach().reshape(-1) for p in model.parameters()])
    delta=float((flat-reference_flat).abs().max())
    if not torch.allclose(loss.detach(),reference.detach(),atol=2e-6,rtol=2e-6): raise AssertionError('Original R46 CE differs')
    if not torch.allclose(flat,reference_flat,atol=2e-5,rtol=2e-5): raise AssertionError('Original R46 CE gradients differ')
    record.update(originalCeSourceSha256=sha(source),originalCeScalarAbsoluteError=float((loss-reference).detach().abs()),
        originalCeGradientMaximumAbsoluteError=delta,originalCeReferencePassed=True)
    opt.zero_grad(set_to_none=True)
    after=digest(dict(model=model.state_dict(),optimizer=opt.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate()))
    if before!=after: raise AssertionError('Preflight changed model/Adam/RNG')
    record['modelOptimizerRngUnchanged']=True
    return record


def run(panel_path,panel_sha,plan_path,plan_sha,output,arm,preflight_only=False):
    if sha(panel_path)!=panel_sha or sha(plan_path)!=plan_sha: raise ValueError('Frozen plan/panel mismatch')
    panel=json.loads(pathlib.Path(panel_path).read_text()); plan=json.loads(pathlib.Path(plan_path).read_text())
    if plan['panelSha256']!=panel_sha: raise ValueError('Plan panel binding mismatch')
    if not preflight_only and plan.get('trainingAuthorized') is not True:
        raise ValueError('Frozen plan does not authorize optimizer updates')
    for name,expected in plan['codeReceipts'].items():
        if sha(REPO/name)!=expected: raise ValueError('Frozen code changed: '+name)
    rows=[dict(r,prefixTokens=r['conditions']['correct']['prefixTokens'],
        wrongPrefixTokens=r['conditions']['mismatched']['prefixTokens'],targetTokens=r['goldTokens'])
        for r in panel['cases'] if r['group']=='fit']
    if len(rows)!=64 or len({r['id'] for r in rows})!=64: raise ValueError('Exactly64 distinct fit examples required')
    for r in rows:
        if len(r['prefixTokens'])!=len(r['wrongPrefixTokens']): raise ValueError('Unequal context lengths')
    output=pathlib.Path(output); output.mkdir(parents=True,exist_ok=True)
    ledger=output/'optimizer-ledger.jsonl'
    if ledger.exists() or (output/'terminal.pt').exists(): raise ValueError('Refuse repeat execution')
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    model,opt,rng=load_initial(); initial_model=digest(model.state_dict()); initial_opt=digest(opt.state_dict())
    preflight=first_batch_preflight(model,opt,rng,rows,arm)
    (output/'preflight.json').write_text(json.dumps(preflight,indent=2,allow_nan=False)+'\n')
    if preflight_only: return dict(arm=arm,preflight=preflight,actualOptimizerUpdates=0)
    order=[]; cursor=0; history=[]; actual=0; mid=output/'resume-step2.pt'; reference=None; resume={}
    def emit(row):
        with ledger.open('a') as f: f.write(json.dumps(row,allow_nan=False)+'\n'); f.flush()
    def update(unique,replay=False):
        nonlocal order,cursor,actual
        if cursor>=len(order): order=list(range(64)); rng.shuffle(order); cursor=0
        ids=order[cursor:cursor+8]; cursor+=8
        opt.zero_grad(set_to_none=True); before=torch.get_rng_state().clone()
        loss,record=response_ce(model,[rows[i] for i in ids],arm)
        if not torch.equal(before,torch.get_rng_state()): raise AssertionError('CE consumed Torch RNG')
        if not bool(torch.isfinite(loss)): raise ValueError('Nonfinite CE; stopped before step')
        loss.backward(); params=list(model.parameters())
        if any(p.grad is None or not bool(torch.isfinite(p.grad).all()) for p in params): raise ValueError('Invalid gradient')
        norm=torch.nn.utils.clip_grad_norm_(params,1.,error_if_nonfinite=True)
        if actual>=200: raise RuntimeError('Hard actual-update budget exhausted')
        emit(dict(event='before-step',actualUpdate=actual+1,uniqueUpdate=unique,replay=replay))
        opt.step(); actual+=1
        emit(dict(event='after-step',actualUpdate=actual,uniqueUpdate=unique,replay=replay))
        if any(not bool(torch.isfinite(p).all()) for p in params): raise ValueError('Nonfinite updated model')
        record.update(uniqueUpdate=unique,loss=float(loss.detach()),ids=[rows[i]['id'] for i in ids],
            preclipGradientNorm=float(norm),clipped=bool(norm>1),modelDigest=digest(model.state_dict()),
            optimizerDigest=digest(opt.state_dict()),torchRngDigest=digest(torch.get_rng_state()),pythonRngDigest=digest(rng.getstate()))
        return record
    for unique in range(1,199):
        history.append(update(unique))
        if unique==2: torch.save(snapshot(model,opt,rng,order,cursor,history,unique),mid)
        if unique==4:
            reference=snapshot(model,opt,rng,order,cursor,history,unique)
            mid_sha=sha(mid); saved=torch.load(mid,map_location='cpu',weights_only=False)
            # Recreate both objects before loading actual serialized state.
            del model,opt,rng
            model,opt,rng=load_initial(); model.load_state_dict(saved['model']); opt.load_state_dict(saved['optimizer'])
            rng.setstate(saved['pythonRng']); torch.set_rng_state(saved['torchRng']); model.train(saved['modelTraining'])
            order=saved['order']; cursor=saved['cursor']; history=saved['history']
            if not exact(snapshot(model,opt,rng,order,cursor,history,2),saved): raise AssertionError('Reload differs')
            history.extend([update(3,True),update(4,True)])
            if not exact(snapshot(model,opt,rng,order,cursor,history,4),reference): raise AssertionError('Resume trajectory differs')
            resume=dict(passed=True,midpointSha256=mid_sha,replayActualUpdates=2,allStateAndTraceBitwiseEqual=True)
            mid.unlink(); reference=None
    if actual!=200 or len(history)!=198: raise AssertionError('Incorrect update accounting')
    terminal=snapshot(model,opt,rng,order,cursor,history,198)
    terminal.update(arm=arm,scope='Disposable learnability assay; never adopt',actualOptimizerUpdates=actual,
        replayOptimizerUpdates=2,initialCheckpointSha256=CHECKPOINT_SHA,panelSha256=panel_sha,planSha256=plan_sha)
    torch.save(terminal,output/'terminal.pt')
    receipt=dict(arm=arm,uniqueUpdates=198,actualOptimizerUpdates=actual,replayOptimizerUpdates=2,
        initialModelDigest=initial_model,initialOptimizerDigest=initial_opt,resume=resume,
        zeroUpdatePreflight=preflight,
        terminalSha256=sha(output/'terminal.pt'),initialCheckpointUnchanged=sha(CHECKPOINT)==CHECKPOINT_SHA,
        finalAdamCounters=sorted({float(v['step']) for v in opt.state_dict()['state'].values()}),
        panelSha256=panel_sha,planSha256=plan_sha,history=history)
    (output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--panel',required=True); p.add_argument('--panel-sha256',required=True)
    p.add_argument('--plan',required=True); p.add_argument('--plan-sha256',required=True)
    p.add_argument('--output',required=True); p.add_argument('--arm',choices=['A','B'],required=True)
    p.add_argument('--preflight-only',action='store_true')
    a=p.parse_args(); result=run(a.panel,a.panel_sha256,a.plan,a.plan_sha256,a.output,a.arm,a.preflight_only)
    print(json.dumps({k:v for k,v in result.items() if k!='history'}))
