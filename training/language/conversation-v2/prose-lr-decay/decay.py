"""Isolate the change in the last 150 AdamW learning rates."""
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'prose-learning-rate'
sys.path.insert(0,str(OLD))
from protocol import read,save,sha
spec=importlib.util.spec_from_file_location('lr_runner', OLD/'run.py')
lr=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lr)
torch=lr.torch
restore=lr.previous.restore
archive=lr.previous.checkpoint
digest=lr.engine.digest
old=read(OLD/'B-ledger.json')
base=read(OLD/'PLAN.json')

def freeze():
    rates=dict(A=[3e-5]*150,B=[3e-6+1.35e-5*(1+math.cos(math.pi*i/149)) for i in range(150)],C=[1.65e-5]*150)
    rates['B'][0],rates['B'][-1]=3e-5,3e-6
    assert math.isclose(math.fsum(rates['B'])/150,1.65e-5,abs_tol=1e-20)
    save(ROOT/'PLAN.json',dict(rates=rates,steps=[150,175,200,250,300],checkpoints=[200,300],
         initial=base['baseline'],inherited={str(p.relative_to(ROOT.parent)):sha(p) for p in [
         OLD/'PLAN.json',OLD/'B-ledger.json',OLD/'INPUTS.json',OLD/'run.py',
         *[OLD/f'artifacts/B-{k}/checkpoint.json' for k in (100,200,300)],
         *[OLD/f'B-{k}.json.gz' for k in (150,200,250,300)]]},
         evaluation='Inherited full-vocabulary greedy, fixed 18+7 prose and 32 captions, same 14 common TRAIN and fixed 32 sampled TRAIN. No outcome-driven changes.'))
    (ROOT/'PLAN.sha256').write_text(sha(ROOT/'PLAN.json')+'\n')

def validate():
    plan=read(ROOT/'PLAN.json')
    assert sha(ROOT/'PLAN.json')==(ROOT/'PLAN.sha256').read_text().strip()
    for p,h in plan['inherited'].items():assert sha(ROOT.parent/p)==h
    return plan

def update(model,opt,arm,k,initial,observe=False):
    lr_value=read(ROOT/'PLAN.json')['rates'][arm][k-151] if k>150 else 3e-5
    opt.param_groups[0]['lr']=lr_value
    if not observe:return lr.update(model,opt,k)
    x,y,group,denominator=lr.engine.batch_for('C',k)
    opt.zero_grad(set_to_none=True)
    logits=model(x)
    losses=torch.nn.functional.cross_entropy(logits.flatten(0,1),y.flatten(),reduction='none').reshape_as(y)
    prose=float(losses[group==0].sum().detach())/denominator
    replay=float(losses[group==1].sum().detach())/denominator
    # Preserve the inherited sum-reduction kernel and its gradient exactly.
    loss=torch.nn.functional.cross_entropy(logits.flatten(0,1),y.flatten(),reduction='sum')/denominator
    assert torch.isfinite(loss)
    loss.backward()
    norm=float(lr.engine.clip_grad_accurate(model.parameters(),1.))
    before=[p.detach().clone() for p in model.parameters()]
    opt.step()
    delta=math.sqrt(math.fsum(float((p.detach()-q).double().square().sum()) for p,q in zip(model.parameters(),before)))
    distance=lr.displacement(model,initial)
    assert math.isfinite(delta) and math.isfinite(distance['total'])
    return dict(step=k,lr=lr_value,loss=float(loss.detach()),prose_loss_contribution=prose,replay_loss_contribution=replay,
                norm=norm,post_clip_norm=norm*min(1,1/(norm+1e-6)),clipped=norm>1,delta=delta,
                distance=distance['total'],prose=int((group==0).sum()),replay=int((group==1).sum()),
                denominator=denominator,shape=list(x.shape),non_pad=int(x.ne(0).sum()),
                adam_step=int(next(iter(opt.state.values()))['step']),nonfinite=False)

def detect(model,key):
    saved=lr.engine.batch_for
    try:
        lr.engine.batch_for=lambda *_:lr.broad.diagnostic_batch
        save(ROOT/f'{key}-grad.json',lr.engine.diagnosis(model))
    finally:
        lr.engine.batch_for=saved

def signature(m,o):
    return digest([m.state_dict(),o.state_dict(),torch.get_rng_state()])

def recover(initial):
    m,o,_=restore(OLD/'artifacts/B-100')
    for k in range(101,301):
        r=update(m,o,'A',k,initial,observe=k>150)
        assert all(r[f]==v for f,v in old[k-1].items()), (k,r,old[k-1])
        if k==150:
            archive(m,o,k,old[:k],ROOT/'artifacts/common-150')
            detect(m,'common-150')
        if k>150:
            ledger.append(r)
        if k==175:
            torch_rng=torch.get_rng_state().clone()
            evaluate(m,'A',k,initial)
            torch.set_rng_state(torch_rng)
    actual=signature(m,o)
    m,o,_=restore(OLD/'artifacts/B-300')
    assert actual==signature(m,o)
    save(ROOT/'A-ledger.json',ledger)
    save(ROOT/'RECOVERY.json',dict(reconstructed_calls=200,terminal_state_digest=actual,matched_steps=[101,300]))

def evaluate(m,arm,k,initial):
    lr.broad.ROOT=ROOT
    lr.broad.plan['arms'][arm]=lr.broad.plan['arms']['C']
    lr.broad.stats(m,arm,k)
    lr.broad.generate(m,arm,k)
    save(ROOT/f'{arm}-{k}-distance.json',lr.displacement(m,initial))
    if k in (200,300):
        detect(m,f'{arm}-{k}')

def train(arm,initial):
    m,o,_=restore(ROOT/'artifacts/common-150')
    rows=[]
    for k in range(151,301):
        r=update(m,o,arm,k,initial,observe=True)
        r['path_from_150']=math.fsum(x['delta'] for x in rows)+r['delta']
        rows.append(r)
        if k in (175,200,250,300):
            save(ROOT/f'{arm}-ledger.json',rows)
            evaluate(m,arm,k,initial)
        if k in (200,300):
            folder=ROOT/'artifacts'/f'{arm}-{k}'
            archive(m,o,k,old[:150]+rows,folder)
            if k==200:
                observed=json.loads(subprocess.check_output([sys.executable,__file__,'witness',arm]))
                rng=torch.get_rng_state().clone()
                witness_row=update(m,o,arm,201,initial,observe=True)
                assert observed==dict(row=witness_row,digest=signature(m,o))
                # Recover the 200-step state so the ordinary loop retains update 201.
                m,o,_=restore(folder)
                assert torch.equal(torch.get_rng_state(),rng)
                save(ROOT/f'{arm}-resume.json',observed)
    save(ROOT/f'{arm}-receipt.json',dict(retained=150,witness_calls=2,total_calls=152))

def main():
    mode=sys.argv[1]
    if mode=='freeze':
        freeze()
        return
    validate()
    initial={n:p.detach().clone() for n,p in lr.previous.initial('initial').named_parameters()}
    if mode=='recover':
        recover(initial)
    elif mode=='witness':
        arm=sys.argv[2]
        m,o,_=restore(ROOT/f'artifacts/{arm}-200')
        row=update(m,o,arm,201,initial,True)
        print(json.dumps(dict(row=row,digest=signature(m,o))))
    else:
        assert (ROOT/'RECOVERY.json').exists()
        train(mode,initial)

ledger=[]
if __name__=='__main__':
    main()
