"""Validate the evidence and cold-restored inherited training state."""
import math
import sys
from collections import Counter
from probe import BASE, OLD, ROOT, read, sha

def main():
    plan=read(ROOT/'PLAN.json')
    assert sha(ROOT/'PLAN.json')==(ROOT/'PLAN.sha256').read_text().strip()
    assert sha(ROOT/'SITES.json')==plan['sites_sha256']
    for name,expected in plan['inherited'].items():
        assert sha(BASE/name)==expected
    sites=read(ROOT/'SITES.json')
    candidates=read(ROOT/'CANDIDATES.json')
    review=read(ROOT/'REVIEW.json')
    typography=read(ROOT/'TYPOGRAPHY.json')
    rows=read(OLD/'TRAIN.json')
    pieces=list(map(bytes.fromhex,read(BASE/'data/tokenizer.json')['bytes']))
    assert len({s['family'] for s in sites})==30
    decode=lambda tokens: b''.join(pieces[t] for t in tokens)
    expected_review=set()
    counts=Counter()
    for s,r,t in zip(sites,candidates['results'],typography['cases'],strict=True):
        source=rows[s['index']]
        assert s['id']==r['id']==t['id']==source['id']
        assert s['prefix']+s['replaced']==source['prefix']
        assert s['reference']==source['gold']
        assert len(r['generated'])==len(r['p_greedy'])
        assert all(0<v<=1 for v in r['p_greedy'])
        assert [c['length'] for c in r['candidates']]==plan['lengths']
        for c in r['candidates']:
            assert c['tokens']==r['generated'][:c['length']]
            assert decode(c['tokens']).hex()==c['raw_hex']
            counts[c['rule']]+=1
            if c['rule']=='requires_semantic_review':
                expected_review.add((s['id'],c['length']))
        before=decode(t['prefix_original']).decode()
        after=decode(t['prefix_variant']).decode()
        assert before==decode(source['prefix']).decode()
        assert after==t['variant'] and len(before)==len(after)
        assert sum(a!=b for a,b in zip(before,after))==1
        assert t['gold']==source['gold'][:32]
        assert len(t['nll_original'])==len(t['nll_variant'])==32
        assert all(math.isfinite(v) for v in t['nll_original']+t['nll_variant'])
    checks=review['semantic_review']
    assert expected_review=={(r['id'],r['length']) for r in checks}
    assert counts=={'requires_semantic_review':3,'not_complete_single_clause':117}
    assert not any(r['accept'] for r in checks)
    assert sum(len(r['generated']) for r in candidates['results'])==candidates['forwards']==480
    assert typography['forwards']==60
    assert plan['optimizer_updates']==candidates['optimizer_calls']==typography['optimizer_calls']==0
    assert review['comparison']['optimizer_ledger']==[]
    sys.path.insert(0,str(OLD))
    from run_budget import parent
    from verify_budget import recover
    ledger=read(OLD/'LEDGER.json')
    previous=None
    for n,folder,evidence in zip((300,600),(parent,OLD/'artifacts/C-600'),candidates['checkpoints'],strict=True):
        st=recover(folder)
        assert st['uniqueUpdates']==evidence['step']==len(st['history'])==n
        assert {int(x['step']) for x in st['optimizer']['state'].values()}=={n}
        assert read(folder/'checkpoint.json')['sha256']==evidence['checkpoint_sha256']
        if previous is not None:
            assert previous+ledger==st['history']
        previous=st['history']
    print('PASS: schedule lineage, cold checkpoints, 120 candidate decisions and 960 typography comparisons')

if __name__=='__main__':
    main()
