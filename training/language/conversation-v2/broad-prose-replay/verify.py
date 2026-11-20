"""Check frozen inputs and restore all four complete checkpoints from Git."""
import gzip
import hashlib
import io
import json
from collections import Counter
import torch
from build import ROOT, BASE, OLD, FAMILY, archive, read, sha
from audit import audit

def main():
    plan=read(ROOT/'PLAN.json')
    assert sha((ROOT/'PLAN.json').read_bytes())==(ROOT/'PLAN.sha256').read_text().strip()
    for f,h in plan['frozen'].items():assert sha((ROOT/f).read_bytes())==h
    assert sha((OLD/'SCHEDULE.json').read_bytes())==plan['fixed_replay_SHA']
    assert sha((OLD/'REPLAY.json').read_bytes())==plan['replay_SHA']
    baseline=read(OLD/'PLAN.json')
    assert baseline['baseline']==plan['baseline'] and baseline['seed']==plan['seed'] and baseline['lr']==.0001
    assert read(OLD/'C-receipt.json')['retained']==300
    assert read(OLD/'C-ledger.json')[299]['step']==300
    audit()
    b=read(ROOT/'B-ledger.json')
    c=read(ROOT/'C-ledger.json')
    assert b[:84]==c[:84]
    assert b[84]['step']==85 and b[84]!=c[84]

    pieces=[bytes.fromhex(t) for t in read(BASE/'data/tokenizer.json')['bytes']]
    for arm,batches in read(ROOT/'SCHEDULE.json').items():
        ledger=read(ROOT/f'{arm}-ledger.json')
        assert len(ledger)==300
        assert read(ROOT/f'{arm}-receipt.json')=={'retained':300,'optimizer_calls':301}
        assert read(ROOT/f'{arm}-resume.json')['row']==ledger[100]
        for k,(b,row) in enumerate(zip(batches,ledger,strict=True),1):
            assert row['step']==k and row['denominator']==b['denominator']
            assert row['prose']==sum(n for _,_,n in b['prose'])
            assert row['replay']==sum(n for _,_,n in b['replay'])
        for step in plan['steps'][1:]:
            with gzip.open(ROOT/f'{arm}-{step}.json.gz') as stream:
                rows=json.load(stream)['cases']
            assert Counter(r['panel'] for r in rows)=={'prose':25,'train':14,'caption':32}
            for r in rows:
                assert b''.join(pieces[t] for t in r['generated']).hex()==r['raw_hex']
                assert r['generated']==[s['top5'][0][0] for s in r['steps']]
                assert not r['forced'] and len(r['generated'])<=r['budget']
        for step in (100,300):
            folder=ROOT/'artifacts'/f'{arm}-{step}'
            manifest=read(folder/'checkpoint.json')
            buf=io.BytesIO()
            h=hashlib.sha256()
            for part in manifest['chunks']:
                raw=archive(str((folder/part['path']).relative_to(BASE)))
                assert sha(raw)==part['sha256']
                buf.write(raw)
                h.update(raw)
            assert h.hexdigest()==manifest['sha256']
            buf.seek(0)
            state=torch.load(buf,map_location='cpu',weights_only=False)['trajectory']
            assert state['history']==ledger[:step] and state['uniqueUpdates']==step
            assert {int(v['step']) for v in state['optimizer']['state'].values()}=={step}
    print('PASS exact replay schedules, generation records and four complete Git-only states')

if __name__=='__main__':main()
