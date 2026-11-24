"""Reuse the exact replay optimizer and archived greedy evaluator."""
import json
import subprocess
import sys
from pathlib import Path
from build import ROOT,BASE,OLD,FAMILY,read,save,sha

sys.path.insert(0,str(OLD))
import importlib.util
spec=importlib.util.spec_from_file_location('replay_runner',OLD/'run.py')
engine=importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
torch=engine.torch
previous=engine.previous
evaluation=engine.evaluation
plan=read(ROOT/'PLAN.json')
assert sha((ROOT/'PLAN.json').read_bytes())==(ROOT/'PLAN.sha256').read_text().strip()
assert sha((OLD/'SCHEDULE.json').read_bytes())==plan['fixed_replay_SHA']
assert sha((OLD/'REPLAY.json').read_bytes())==plan['replay_SHA']
for f,h in plan['frozen'].items():
    assert sha((ROOT/f).read_bytes())==h
new_train=read(ROOT/'TRAIN.json')
new_schedule=read(ROOT/'SCHEDULE.json')
diagnostic_batch=engine.batch_for('C',1)
new_dev=[dict(r,tokens=r['prefix']+r['gold'],teacher_continuation=r['gold'][:32]) for r in read(ROOT/'NEW_DEV.json')]
original_eval=evaluation.ev

def configure():
    engine.train=new_train
    engine.schedule=new_schedule

def stats(model,arm,step):
    dirty=model.training
    model.eval()
    sample=plan['arms'][arm][14::max(1,(len(plan['arms'][arm])-14)//32)][:32]
    with torch.inference_mode():
        total=count=0
        for i in sample:
            r=new_train[i]
            x=r['prefix']+r['gold']
            logits=model(torch.tensor([x[:-1]]))[0,len(r['prefix'])-1:]
            gold=torch.tensor(r['gold'])
            mask=(gold!=16)&(gold!=2)
            total+=float(torch.nn.functional.cross_entropy(logits[mask],gold[mask],reduction='sum'))
            count+=int(mask.sum())
    model.train(dirty)
    save(ROOT/f'{arm}-{step}-sample.json',dict(ids=sample,targets=count,nll=total/count,**engine.replay_nll(model)))
    if step in (0,100,300):
        batch_for=engine.batch_for
        try:
            engine.batch_for=lambda *_:diagnostic_batch
            save(ROOT/f'{arm}-{step}-grad.json',engine.diagnosis(model))
        finally:
            engine.batch_for=batch_for

def generate(model,arm,step,only_new=False):
    evaluation.P=ROOT
    evaluation.train=[] if only_new else new_train[:14]
    evaluation.plan={'models':{}}
    evaluation.ev=dict(prose=new_dev if only_new else original_eval['prose']+new_dev,
                       caption=[] if only_new else original_eval['caption'])
    evaluation.restore=lambda _: (model,None,None)
    evaluation.evaluate(f'{arm}-{step}')
    model.train()

def main(arm):
    if arm=='A':
        for step in (0,300):
            m=previous.initial('initial') if not step else previous.restore(OLD/'artifacts/C-300')[0]
            generate(m,arm,step,only_new=True)
        return
    configure()
    model=previous.initial('initial')
    optimizer=previous.optimizer(model)
    torch.manual_seed(plan['seed'])
    log=[]
    for step in plan['steps']:
        for k in range(len(log)+1,step+1):
            log.append(engine.update(model,optimizer,arm,k))
        save(ROOT/f'{arm}-ledger.json',log)
        if step in (100,300):
            folder=ROOT/'artifacts'/f'{arm}-{step}'
            previous.checkpoint(model,optimizer,step,log,folder)
            if step==100:
                result=json.loads(subprocess.check_output([sys.executable,__file__,'witness',arm,str(folder)]))
                row=engine.update(model,optimizer,arm,101)
                assert result==dict(row=row,digest=engine.digest([model.state_dict(),optimizer.state_dict(),torch.get_rng_state()]))
                log.append(row)
                rng=torch.get_rng_state().clone()
                restored,_,_=previous.restore(folder)
                stats(restored,arm,step)
                generate(restored,arm,step)
                torch.set_rng_state(rng)
                save(ROOT/f'{arm}-resume.json',result)
                continue
        stats(model,arm,step)
        if step:
            generate(model,arm,step)
    save(ROOT/f'{arm}-receipt.json',dict(retained=len(log),optimizer_calls=len(log)+1))

if __name__=='__main__':
    if sys.argv[1]=='witness':
        configure()
        engine.witness(sys.argv[2],100,Path(sys.argv[3]))
    else:
        main(sys.argv[1])
