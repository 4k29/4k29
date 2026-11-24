"""Verify inherited evidence, schedule equality and complete Git-only checkpoints."""
import gzip
import hashlib
import io
import json
import math
import subprocess
from collections import Counter
import torch
from measure import ROOT,BASE,OLD,read,raw

def checksum(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def recover(name,step,ledger):
    folder=ROOT/'artifacts'/name
    manifest=read(folder/'checkpoint.json')
    repo=ROOT.parents[3]
    binary=io.BytesIO()
    h=hashlib.sha256()
    for part in manifest['chunks']:
        path=(folder/part['path']).relative_to(repo)
        content=subprocess.check_output(['git','show',f'HEAD:{path}'],cwd=repo)
        assert hashlib.sha256(content).hexdigest()==part['sha256']
        h.update(content)
        binary.write(content)
    assert h.hexdigest()==manifest['sha256']
    binary.seek(0)
    state=torch.load(binary,map_location='cpu',weights_only=False)['trajectory']
    assert state['history']==ledger and state['uniqueUpdates']==step
    assert {int(v['step']) for v in state['optimizer']['state'].values()}=={step}
    return state['optimizer']['param_groups'][0]['lr']

def main():
    plan=read(ROOT/'PLAN.json')
    assert checksum(ROOT/'PLAN.json')==(ROOT/'PLAN.sha256').read_text().strip()
    for p,h in plan['inherited'].items():
        assert checksum(BASE/p)==h
    assert read(ROOT/'RECOVERY.json')['reconstructed_calls']==200
    assert math.isclose(math.fsum(plan['rates']['B'])/150,1.65e-5,abs_tol=1e-20)
    past=read(OLD/'B-ledger.json')
    assert recover('common-150',150,past[:150])==3e-5
    pieces=[bytes.fromhex(t) for t in read(BASE/'data/tokenizer.json')['bytes']]
    for arm in 'ABC':
        rows=read(ROOT/f'{arm}-ledger.json')
        assert len(rows)==150
        for a,b,rate in zip(past[150:],rows,plan['rates'][arm],strict=True):
            assert b['lr']==rate and b['adam_step']==b['step'] and not b['nonfinite']
            assert all(a[f]==b[f] for f in ('step','prose','replay','denominator','shape','non_pad'))
            assert abs(b['prose_loss_contribution']+b['replay_loss_contribution']-b['loss']) < 1e-5
            if arm=='A':assert all(b[k]==v for k,v in a.items())
        for k in plan['steps']:
            output=raw(arm,k)['cases']
            assert Counter(r['panel'] for r in output)=={'prose':25,'train':14,'caption':32}
            for row in output:
                assert not row['forced']
                assert row['generated']==[step['top5'][0][0] for step in row['steps']]
                assert b''.join(pieces[t] for t in row['generated']).hex()==row['raw_hex']
        if arm=='A':continue
        receipt=read(ROOT/f'{arm}-receipt.json')
        assert receipt['retained']==150 and receipt['witness_calls']==2
        if arm=='B':assert receipt['total_calls']==152
        else:assert receipt['confirmed_total_calls']==202 and receipt['confirmed_reconstruction_calls']==50
        check=read(ROOT/f'{arm}-resume.json')['row']
        assert all(rows[50][key]==value for key,value in check.items())
        for k in (200,300):
            assert recover(f'{arm}-{k}',k,past[:150]+rows[:k-150])==plan['rates'][arm][k-151]
    assert read(ROOT/'CALLS.json')['confirmed_optimizer_total']==554
    print('PASS exact inherited evidence, equal teacher schedules, generations and five complete Git-only checkpoints')

if __name__=='__main__':main()
