"""Train on the fixed schedule and preserve complete continuation state."""
import json
import math
import subprocess
import sys
from collections import defaultdict
from prepare import ROOT, BASE, FAMILY, PREVIOUS, read, save, sha

sys.path.insert(0,str(PREVIOUS))
import experiment as previous
import evaluate as evaluation
import torch
from core import clip_grad_accurate, digest

plan=read(ROOT/'PLAN.json')
assert sha((ROOT/'PLAN.json').read_bytes())==(ROOT/'PLAN.sha256').read_text().strip()
for name,h in plan['frozen'].items():
    assert sha((ROOT/name).read_bytes())==h
for path,key in [(FAMILY/'TRAIN.json','train_SHA'),(FAMILY/'SCHEDULE.json','A_schedule_SHA'),
                 (BASE/'gv-prose-pilot/EVALUATION_INPUTS.json','eval_SHA')]:
    assert sha(path.read_bytes())==plan[key]
train=read(FAMILY/'TRAIN.json')
replay=read(ROOT/'REPLAY.json')
monitor=read(ROOT/'MONITOR.json')
schedule=read(ROOT/'SCHEDULE.json')
schedule['A']=[dict(prose=b,replay=[],denominator=sum(n for _,_,n in b))
               for b in read(FAMILY/'SCHEDULE.json')['C']]

def batch_for(arm, step):
    batch=schedule[arm][step-1]
    captions=schedule['C'][step-1]['replay'] if arm=='D' else batch['replay']
    entries=[(train,i,s,n,0) for i,s,n in batch['prose']]
    entries.extend((replay,i,s,n,2 if arm=='D' else 1) for i,s,n in captions)
    seqs=[torch.tensor(records[i]['prefix']+records[i]['gold'][:s+n]) for records,i,s,n,_ in entries]
    seq=torch.nn.utils.rnn.pad_sequence(seqs,batch_first=True)
    y=torch.full_like(seq[:,1:],-100)
    group=torch.full_like(y,-1)
    for row,(records,i,start,n,kind) in enumerate(entries):
        if kind==2:
            continue
        offset=len(records[i]['prefix'])-1+start
        y[row,offset:offset+n]=seq[row,offset+1:offset+n+1]
        group[row,offset:offset+n]=kind
    assert int((group==0).sum())==sum(n for _,_,n in batch['prose'])
    assert int((group==1).sum())==sum(n for _,_,n in batch['replay'])
    return seq[:,:-1],y,group,batch['denominator']

def update(model,optimizer,arm,k):
    x,y,group,denominator=batch_for(arm,k)
    optimizer.zero_grad(set_to_none=True)
    logits=model(x)
    if arm=='A':
        # Match the archived control, including its exact reduction path.
        loss=previous.causal_ce(logits,y)
    else:
        summed=torch.nn.functional.cross_entropy(logits.flatten(0,1),y.flatten(),reduction='sum')
        loss=summed/denominator
    assert torch.isfinite(loss)
    loss.backward()
    norm=float(clip_grad_accurate(model.parameters(),1.))
    before=[p.detach().clone() for p in model.parameters()]
    optimizer.step()
    delta=math.sqrt(math.fsum(float((p.detach()-old).double().square().sum()) for p,old in zip(model.parameters(),before)))
    assert math.isfinite(delta)
    return dict(step=k,loss=float(loss.detach()),norm=norm,clipped=norm>1,delta=delta,
                prose=int((group==0).sum()),replay=int((group==1).sum()),denominator=denominator,
                shape=list(x.shape),non_pad=int(x.ne(0).sum()))

def diagnosis(model):
    training=model.training
    rng=torch.get_rng_state().clone()
    model.eval()
    x,y,group,_=batch_for('C',1)
    logits=model(x)
    parameters=dict(model.named_parameters())
    gradients=[]
    for kind in (0,1):
        mask=group==kind
        loss=torch.nn.functional.cross_entropy(logits[mask],y[mask])
        gradients.append(torch.autograd.grad(loss,parameters.values(),retain_graph=kind==0))
    by_layer=defaultdict(lambda:[0.,0.,0.,0.])
    total=[0.,0.,0.,0.]
    fraction=float((group==0).sum()/y.ne(-100).sum())
    for name,left,right in zip(parameters,*gradients):
        a,b=left.double(),right.double()
        values=[float(a.square().sum()),float(b.square().sum()),float((a*b).sum()),
                float((a*fraction+b*(1-fraction)).square().sum())]
        layer=name.rsplit('.',1)[0]
        for i,value in enumerate(values):
            by_layer[layer][i]+=value
            total[i]+=value
    def metrics(values):
        aa,bb,dot,mix=values
        return dict(prose_norm=math.sqrt(aa),replay_norm=math.sqrt(bb),dot=dot,
                    cosine=dot/math.sqrt(aa*bb) if aa and bb else None,
                    mixed_norm=math.sqrt(mix),mixed_norm_clipped_global=min(math.sqrt(mix),1.))
    assert torch.equal(rng,torch.get_rng_state())
    model.train(training)
    return dict(global_metrics=metrics(total),layers={n:metrics(v) for n,v in by_layer.items()},
                tied_embedding_output=True,diagnostic_optimizer_calls=0)

@torch.inference_mode()
def replay_nll(model):
    training=model.training
    model.eval()
    def nll(rows):
        sequences=[torch.tensor(r['prefix']+r['gold']) for r in rows]
        x=torch.nn.utils.rnn.pad_sequence(sequences,batch_first=True)
        y=x[:,1:].clone()
        y[y==0]=-100
        return float(torch.nn.functional.cross_entropy(model(x[:,:-1]).flatten(0,1),y.flatten()))
    data=dict(admitted_replay_first32_nll=nll(replay[:32]),historically_seen_disjoint_monitor_nll=nll(monitor))
    model.train(training)
    return data

def assess(model,arm,step,generate=True):
    save(ROOT/f'{arm}-{step}-nll.json',replay_nll(model))
    if step in plan['diagnostic_steps']:
        save(ROOT/f'{arm}-{step}-grad.json',diagnosis(model))
    if generate:
        evaluation.P=ROOT
        evaluation.train=[train[i] for i in read(FAMILY/'PLAN.json')['arms']['C']]
        evaluation.plan={'models':{}}
        evaluation.restore=lambda _: (model,None,None)
        evaluation.evaluate(f'{arm}-{step}')
        model.train()

def witness(arm,step,location):
    model,optimizer,state=previous.restore(location)
    row=update(model,optimizer,arm,step+1)
    print(json.dumps(dict(row=row,digest=digest([model.state_dict(),optimizer.state_dict(),torch.get_rng_state()]))))

def main(arm):
    model=previous.initial('initial')
    initial=digest(model.state_dict())
    optimizer=previous.optimizer(model)
    torch.manual_seed(plan['seed'])
    log=[]
    if arm=='A':
        assess(model,arm,0,False)
        for step in range(1,11):
            log.append(update(model,optimizer,arm,step))
        reference=read(FAMILY/'C-ledger.json')
        assert all(x['loss']==y['loss'] and x['norm']==y['norm'] for x,y in zip(log,reference[:10]))
        assess(model,arm,10)
        for step in (20,50,100,200,300):
            checkpoint=FAMILY/'artifacts'/f'C-{step}'
            if step in (100,300):
                model,_,_=previous.restore(checkpoint)
                assess(model,arm,step,False)
        save(ROOT/'A-prefix-ledger.json',log)
        return
    for step in plan['steps']:
        for k in range(len(log)+1,step+1):
            log.append(update(model,optimizer,arm,k))
        save(ROOT/f'{arm}-ledger.json',log)
        if step in plan['save_steps']:
            folder=ROOT/'artifacts'/f'{arm}-{step}'
            previous.checkpoint(model,optimizer,step,log,folder)
            if step==100:
                expected=json.loads(subprocess.check_output([sys.executable,__file__,'witness',arm,str(step),str(folder)]))
                row=update(model,optimizer,arm,101)
                assert expected==dict(row=row,digest=digest([model.state_dict(),optimizer.state_dict(),torch.get_rng_state()]))
                log.append(row)
                rng=torch.get_rng_state().clone()
                restored,_,_=previous.restore(folder)
                assess(restored,arm,step)
                torch.set_rng_state(rng)
                save(ROOT/f'{arm}-resume.json',expected)
                continue
        assess(model,arm,step,generate=step!=0)
    save(ROOT/f'{arm}-receipt.json',dict(initial_sha=initial,retained=len(log),optimizer_calls=len(log)+1))

if __name__=='__main__':
    if sys.argv[1]=='witness':
        from pathlib import Path
        witness(sys.argv[2],int(sys.argv[3]),Path(sys.argv[4]))
    else:
        main(sys.argv[1])
