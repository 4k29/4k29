"""Vary only AdamW learning rate in the PR125 C trajectory."""
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from protocol import ROOT,BASE,SOURCE,read,save,sha

sys.path.insert(0,str(SOURCE))
import importlib.util
spec=importlib.util.spec_from_file_location('broad_runner',SOURCE/'run.py')
broad=importlib.util.module_from_spec(spec)
spec.loader.exec_module(broad)
engine=broad.engine
previous=broad.previous
torch=broad.torch
plan=read(ROOT/'PLAN.json')
assert sha(ROOT/'PLAN.json')==(ROOT/'PLAN.sha256').read_text().strip()
for path,h in plan['frozen'].items():
    assert sha(BASE/path)==h
broad.ROOT=ROOT
broad.plan['diagnostic_steps']=plan['diagnostic_steps']
broad.plan['arms']['A']=broad.plan['arms']['C']
broad.plan['arms']['B']=broad.plan['arms']['C']
broad.configure()
engine.schedule={'C':broad.new_schedule['C']}

def inputs():
    records=[]
    for k in range(1,301):
        x,y,g,d=engine.batch_for('C',k)
        records.append(dict(step=k,sha=engine.digest([x,y,g,d]),shape=list(x.shape),
                            prose=int((g==0).sum()),replay=int((g==1).sum()),denominator=d))
    save(ROOT/'INPUTS.json',records)

def displacement(model,initial):
    layers=defaultdict(float)
    for name,p in model.named_parameters():
        layers[name.rsplit('.',1)[0]]+=float((p.detach()-initial[name]).double().square().sum())
    return dict(total=math.sqrt(math.fsum(layers.values())),layers={k:math.sqrt(v) for k,v in layers.items()},
                tied_embedding_output=True)

def observe(model,initial,arm,k,generate):
    save(ROOT/f'{arm}-{k}-distance.json',displacement(model,initial))
    if arm=='B' or k in (150,200,250):
        broad.stats(model,arm,k)
    if generate:
        broad.generate(model,arm,k)

def update(model,opt,k):
    row=engine.update(model,opt,'C',k)
    row.update(lr=opt.param_groups[0]['lr'],post_clip_norm=row['norm']*min(1.,1./(row['norm']+1e-6)))
    return row

def signature(model,opt,row):
    return dict(row=row,digest=engine.digest([model.state_dict(),opt.state_dict(),torch.get_rng_state()]))

def main(arm):
    model=previous.initial('initial')
    initial={n:p.detach().clone() for n,p in model.named_parameters()}
    initial_sha=engine.digest(model.state_dict())
    opt=previous.optimizer(model)
    assert not opt.state
    opt.param_groups[0]['lr']=plan['lr'][arm]
    torch.manual_seed(plan['seed'])
    if arm=='A':
        reference=read(SOURCE/'C-ledger.json')
        calls=0
        for k in list(range(1,51))+list(range(101,251)):
            if k==101:
                model,opt,_=previous.restore(SOURCE/'artifacts/C-100')
                assert opt.param_groups[0]['lr']==plan['lr']['A']
                observe(model,initial,'A',100,False)
            row=update(model,opt,k)
            calls+=1
            assert all(row[key]==value for key,value in reference[k-1].items()), (k,row,reference[k-1])
            if k in (10,20,50,150,200,250):
                observe(model,initial,'A',k,k in (150,250))
        model,_,_=previous.restore(SOURCE/'artifacts/C-300')
        observe(model,initial,'A',300,False)
        save(ROOT/'A-reconstruction.json',dict(calls=calls,matched_ranges=[[1,50],[101,250]],initial_sha=initial_sha))
        return
    inputs()
    ledger=[]
    for k in plan['steps']:
        for j in range(len(ledger)+1,k+1):
            ledger.append(update(model,opt,j))
        save(ROOT/'B-ledger.json',ledger)
        observe(model,initial,'B',k,k!=0)
        if k not in plan['save_steps']:
            continue
        folder=ROOT/'artifacts'/f'B-{k}'
        previous.checkpoint(model,opt,k,ledger,folder)
        if k==300:
            continue
        check=json.loads(subprocess.check_output([sys.executable,__file__,'verify-resume',str(folder),str(k)]))
        row=update(model,opt,k+1)
        assert check==signature(model,opt,row)
        ledger.append(row)
        save(ROOT/f'B-{k}-resume.json',check)
    save(ROOT/'B-receipt.json',dict(retained=300,optimizer_calls=302,initial_sha=initial_sha))

if __name__=='__main__':
    if sys.argv[1]=='verify-resume':
        m,o,_=previous.restore(Path(sys.argv[2]))
        row=update(m,o,int(sys.argv[3])+1)
        print(json.dumps(signature(m,o,row)))
    else:
        main(sys.argv[1])
