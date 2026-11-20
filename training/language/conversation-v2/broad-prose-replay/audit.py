"""Audit frozen teacher exposure and inherited replay identity."""
from collections import Counter,defaultdict
from statistics import median
from build import ROOT,OLD,read,save,sha

def audit():
    train=read(ROOT/'TRAIN.json')
    new_dev=read(ROOT/'NEW_DEV.json')
    old=read(OLD/'SCHEDULE.json')['C']
    pieces=[bytes.fromhex(t) for t in read(ROOT.parent/'data/tokenizer.json')['bytes']]
    plan=read(ROOT/'PLAN.json')
    results={}
    for arm,batches in read(ROOT/'SCHEDULE.json').items():
        exposure=Counter()
        for a,b in zip(old,batches,strict=True):
            assert a['replay']==b['replay'] and a['denominator']==b['denominator']
            assert sum(n for _,_,n in a['prose'])==sum(n for _,_,n in b['prose'])
            for i,s,n in b['prose']:
                assert i in plan['arms'][arm]
                assert 0<=s<s+n<=len(train[i]['gold'])
                exposure.update((i,t) for t in range(s,s+n))
        docs=Counter()
        families=Counter()
        source=Counter()
        special=Counter()
        known=unknown=0
        for (i,k),n in exposure.items():
            r=train[i]
            docs[r['id']]+=n
            families[r['family']]+=n
            source[r['source']]+=n
            tok=r['gold'][k]
            if tok in (16,2,3,4):special[tok]+=n
            known+=k in r.get('prior_positions',[])
            unknown+='prior_positions' not in r
        ids=plan['arms'][arm]
        assert sum(exposure.values())==46013 and not set(r['family'] for r in new_dev)&set(families)
        results[arm]=dict(independent=len(exposure),processed=sum(exposure.values()),families=len(families),
            units=len(docs),archived_history_overlap=known,prior_position_unresolved=unknown,
            no_match_in_archived_pr105=len(exposure)-known-unknown,min_exposures=min(exposure.values()),
            max_exposures=max(exposure.values()),max_family_share=max(families.values())/46013,
            prefix_median=median(len(train[i]['prefix']) for i in ids),length_median=median(len(train[i]['prefix']+train[i]['gold']) for i in ids),
            sentence_count_median=median(b''.join(pieces[t] for t in train[i]['prefix']+train[i]['gold']).decode().count('。') for i in ids),
            translated_teacher=sum(source[s] for s in source if 'translation' in s),
            source=source,special=special,by_document=docs,by_family=families)
    assert results['C']['max_exposures']==1
    save(ROOT/'DATA_AUDIT.json',results)
    for a,m in results.items():
        print(a,{k:v for k,v in m.items() if not k.startswith('by_')})

if __name__=='__main__':
    audit()
