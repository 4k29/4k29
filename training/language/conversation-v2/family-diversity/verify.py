"""Verify archived CPU runs, token masks, records, and cold checkpoint bytes."""
import gzip
import io
import torch
import hashlib
import json
import subprocess
from collections import Counter
from prepare import ROOT, BASE, read, sha

def verify():
    plan=read(ROOT/'PLAN.json')
    train=read(ROOT/'TRAIN.json')
    batches=read(ROOT/'SCHEDULE.json')
    pieces=[bytes.fromhex(s) for s in read(BASE/'data/tokenizer.json')['bytes']]
    assert sha(ROOT/'PLAN.json')==(ROOT/'PLAN.sha256').read_text().strip()
    for f,h in plan['frozen'].items():
        assert sha(ROOT/f)==h
    hashes=set()
    for arm,ids in plan['arms'].items():
        ledger=read(ROOT/f'{arm}-ledger.json')
        receipt=read(ROOT/f'{arm}-receipt.json')
        hashes.add(receipt['initial_sha'])
        assert len(ledger)==receipt['retained']==300 and receipt['optimizer_calls']==301
        assert read(ROOT/f'{arm}-resume.json')['discarded_calls']==1
        exposures=Counter()
        for step,(batch,entry) in enumerate(zip(batches[arm],ledger,strict=True),1):
            budget=sum(n for _,_,n in batch)
            assert entry['targets']==budget==(307 if step<=225 else 306)
            assert entry['step']==step
            for i,start,count in batch:
                assert i in ids and 0<=start<start+count<=len(train[i]['gold'])
                exposures.update((i,k) for k in range(start,start+count))
        assert sum(exposures.values())==92025
        assert len(exposures)==sum(len(train[i]['gold']) for i in ids)
        for step in plan['steps']:
            rows=json.load(gzip.open(ROOT/f'{arm}-{step}.json.gz'))['cases']
            assert Counter(r['panel'] for r in rows)=={'train':len(ids),'prose':18,'caption':32}
            for r in rows:
                assert b''.join(pieces[t] for t in r['generated']).hex()==r['raw_hex']
                assert [s['top5'][0][0] for s in r['steps']]==r['generated']
                assert len(r['generated'])<=r['budget'] and not r['forced']
        for step in (100,300):
            folder=ROOT/'artifacts'/f'{arm}-{step}'
            manifest=read(folder/'checkpoint.json')
            hash_state=hashlib.sha256()
            archive=io.BytesIO()
            git_root=ROOT.parents[3]
            for part in manifest['chunks']:
                path=(folder/part['path']).relative_to(git_root)
                content=subprocess.check_output(['git','show',f'HEAD:{path}'],cwd=git_root)
                assert hashlib.sha256(content).hexdigest()==part['sha256']
                hash_state.update(content)
                archive.write(content)
            assert hash_state.hexdigest()==manifest['sha256']
            archive.seek(0)
            state = torch.load(archive,map_location='cpu',weights_only=False)['trajectory']
            assert state['uniqueUpdates']==step and state['history']==ledger[:step]
            assert {int(v['step']) for v in state['optimizer']['state'].values()}=={step}
    assert len(hashes)==1
    print('PASS: common initial state, equal teacher budgets, 18 evaluation panels, six Git-only archives')

if __name__=='__main__':
    verify()
