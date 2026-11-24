"""Run the frozen schedules using the PR122 evaluator and checkpoint format."""
import sys
import random
from prepare import ROOT, BASE, PREVIOUS, read, save, sha
sys.path.insert(0,str(PREVIOUS))
import experiment as previous
import evaluate as evaluation
import torch
from core import causal_ce, clip_grad_accurate, digest

plan = read(ROOT/'PLAN.json')
assert sha(ROOT/'PLAN.json') == (ROOT/'PLAN.sha256').read_text().strip()
for path,value in plan['inputs'].items():
    assert sha(BASE/path) == value
for path,value in plan['frozen'].items():
    assert sha(ROOT/path) == value
train = read(ROOT/'TRAIN.json')
schedule = read(ROOT/'SCHEDULE.json')

def update(model, optimizer, arm, step):
    batch = schedule[arm][step-1]
    sequences = [torch.tensor(train[i]['prefix']+train[i]['gold'][:start+count]) for i,start,count in batch]
    x = torch.nn.utils.rnn.pad_sequence(sequences,batch_first=True)
    y = torch.full_like(x[:,1:],-100)
    for n,(i,start,count) in enumerate(batch):
        offset = len(train[i]['prefix'])-1+start
        y[n,offset:offset+count] = x[n,offset+1:offset+count+1]
    targets = int(y.ne(-100).sum())
    assert targets == (307 if step<=225 else 306)
    optimizer.zero_grad(set_to_none=True)
    loss = causal_ce(model(x[:,:-1]),y)
    loss.backward()
    norm = float(clip_grad_accurate(model.parameters(),1.))
    before = [p.detach().clone() for p in model.parameters()]
    optimizer.step()
    delta = sum(float((p.detach()-old).double().square().sum()) for p,old in zip(model.parameters(),before))**.5
    assert __import__('math').isfinite(delta)
    return dict(step=step,targets=targets,loss=float(loss.detach()),norm=norm,clipped=norm>1,delta=delta,
                shape=list(y.shape),non_pad=int(x[:,:-1].ne(0).sum()))

def assess(model, arm, step):
    evaluation.P = ROOT
    evaluation.train = [train[i] for i in plan['arms'][arm]]
    evaluation.plan = {'models':{}}
    evaluation.restore = lambda _: (model,None,None)
    evaluation.evaluate(f'{arm}-{step}')
    model.train()

def main(arm):
    model = previous.initial('initial')
    initial_sha = digest(model.state_dict())
    optimizer = previous.optimizer(model)
    torch.manual_seed(plan['seed'])
    previous.plan['seed']=plan['seed']
    log=[]
    for step in plan['steps']:
        start = len(log)
        for k in range(start+1,step+1):
            log.append(update(model,optimizer,arm,k))
        save(ROOT/f'{arm}-ledger.json',log)
        if step in (100,300):
            folder = ROOT/'artifacts'/f'{arm}-{step}'
            previous.checkpoint(model,optimizer,step,log,folder)
            restored,new_optimizer,state = previous.restore(folder)
            rng = torch.get_rng_state().clone()
            assert digest(model.state_dict()) == digest(restored.state_dict())
            assert digest(optimizer.state_dict()) == digest(new_optimizer.state_dict())
            if step==100:
                probe = update(restored,new_optimizer,arm,101)
                expected = digest([restored.state_dict(),new_optimizer.state_dict(),torch.get_rng_state()])
                torch.set_rng_state(rng)
                retained = update(model,optimizer,arm,101)
                assert probe==retained and expected==digest([model.state_dict(),optimizer.state_dict(),torch.get_rng_state()])
                # Evaluate the checkpoint at step 100, with its RNG restored after eval.
                retained_rng = torch.get_rng_state().clone()
                restored,_,_ = previous.restore(folder)
                assess(restored,arm,step)
                torch.set_rng_state(retained_rng)
                log.append(retained)
                save(ROOT/f'{arm}-resume.json',dict(digest=expected,discarded_calls=1,step=101))
                continue
        assess(model,arm,step)
    save(ROOT/f'{arm}-receipt.json',dict(initial_sha=initial_sha,retained=len(log),optimizer_calls=len(log)+1))

if __name__=='__main__':
    main(sys.argv[1])
