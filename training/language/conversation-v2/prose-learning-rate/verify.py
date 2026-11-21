"""Validate unchanged controls, exact scheduled exposures and full Git states."""
import gzip
import hashlib
import io
import json
import subprocess
from collections import Counter
import torch
from protocol import ROOT,BASE,SOURCE,read,sha

def main():
    plan=read(ROOT/'PLAN.json')
    assert sha(ROOT/'PLAN.json')==(ROOT/'PLAN.sha256').read_text().strip()
    for path,h in plan['frozen'].items():
        assert sha(BASE/path)==h
    source=read(SOURCE/'PLAN.json')
    old=read(SOURCE/'C-ledger.json')
    assert source['baseline']==plan['baseline'] and source['seed']==12103
    assert read(SOURCE/'C-receipt.json')['retained']==300
    ledger=read(ROOT/'B-ledger.json')
    receipt=read(ROOT/'B-receipt.json')
    recovery=read(ROOT/'A-reconstruction.json')
    assert len(ledger)==len(old)==receipt['retained']==300
    assert recovery['initial_sha']==receipt['initial_sha']
    assert recovery['calls']==200 and receipt['optimizer_calls']==302
    assert read(ROOT/'MIDPOINT_RECEIPT.json')=={'A_reconstruction_calls':100,'B_reconstruction_calls':0,'diagnostic_optimizer_calls':0}
    for arm in 'AB':assert read(ROOT/f'{arm}-200-grad.json')['diagnostic_optimizer_calls']==0
    inputs=read(ROOT/'INPUTS.json')
    schedule=read(SOURCE/'SCHEDULE.json')['C']
    assert len(schedule)==len(inputs)==300
    for k,(a,b,batch,entry) in enumerate(zip(old,ledger,schedule,inputs,strict=True),1):
        assert a['step']==b['step']==entry['step']==k
        assert b['lr']==.00003 and len(entry['sha'])==64
        for field in ('shape','non_pad','prose','replay','denominator'):
            assert a[field]==b[field]
        for field in ('prose','replay'):
            assert b[field]==entry[field]==sum(n for _,_,n in batch[field])
        assert entry['denominator']==b['denominator']==batch['denominator']
        assert entry['shape']==b['shape']
    for k in (100,200):
        assert read(ROOT/f'B-{k}-resume.json')['row']==ledger[k]
    pieces=[bytes.fromhex(s) for s in read(BASE/'data/tokenizer.json')['bytes']]
    for arm,steps in [('A',(150,250)),('B',plan['steps'][1:])]:
        for step in steps:
            rows=json.load(gzip.open(ROOT/f'{arm}-{step}.json.gz'))['cases']
            assert Counter(r['panel'] for r in rows)=={'prose':25,'caption':32,'train':14}
            for r in rows:
                assert not r['forced'] and r['generated']==[s['top5'][0][0] for s in r['steps']]
                assert b''.join(pieces[t] for t in r['generated']).hex()==r['raw_hex']
    repo=ROOT.parents[3]
    for k in plan['save_steps']:
        location=ROOT/'artifacts'/f'B-{k}'
        manifest=read(location/'checkpoint.json')
        binary=io.BytesIO()
        digest=hashlib.sha256()
        for part in manifest['chunks']:
            path=(location/part['path']).relative_to(repo)
            raw=subprocess.check_output(['git','show',f'HEAD:{path}'],cwd=repo)
            assert hashlib.sha256(raw).hexdigest()==part['sha256']
            digest.update(raw)
            binary.write(raw)
        assert digest.hexdigest()==manifest['sha256']
        binary.seek(0)
        state=torch.load(binary,weights_only=False,map_location='cpu')['trajectory']
        assert state['history']==ledger[:k] and state['uniqueUpdates']==k
        assert state['optimizer']['param_groups'][0]['lr']==.00003
        assert {int(s['step']) for s in state['optimizer']['state'].values()}=={k}
    print('PASS unchanged source inputs, 300 matched batches, generation files and Git-only checkpoint recovery')

if __name__=='__main__':main()
