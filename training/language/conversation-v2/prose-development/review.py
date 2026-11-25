"""Produce compact shuffled source/output panels and record the single-reader judgment."""
import gzip
import json
import random
import sys
from run import ROOT,OLD,PIECES,read,dump

def raw(path):
    return json.loads(gzip.decompress(path.read_bytes()))['rows']

def stage(name):
    if name=='A-985':
        rows=raw(OLD/'A-985-eval.json.gz')
        x=read(OLD/'A-985-extra.json')['scores']
        for r in rows:
            if r['panel']=='independent':r['panel']='depth24'
            if r['id'] in x:
                g=x[r['id']]
                r.update({k:g[k] for k in ('ref','gold','first')})
                for i,v in g['self_logp'].items():r['steps'][int(i)]['ref']=v
        rows+=raw(ROOT/'monitor-985.json.gz')
    else:rows=raw(ROOT/f'{name}.json.gz')
    return rows

def items(name):
    names=name.split(',')
    rows=[(n,r) for n in names for r in stage(n) if r['panel']!='train']
    random.Random(133000+int(names[-1].split('-')[-1])).shuffle(rows)
    return rows

def print_rows(name,group):
    dev={r['id']:r for r in read(ROOT/'DEV.json')}
    for i,(_,r) in enumerate(items(name)):
        if group=='caption' and r['panel']!='caption':continue
        if group=='prose' and r['panel']=='caption':continue
        txt=r['text']
        prefix=b''.join(PIECES[t] for t in dev[r['id']]['prefix']).decode()
        if txt is None or not txt.strip():continue
        print(i,r['panel'],prefix[-49:].replace('\n',' '), '→',repr(txt[:112]) if r['panel']!='caption' else repr(txt),r['stop'])

def score(name,decisions):
    mapping={int(k):v for k,v in (d.split(':') for d in decisions)}
    path=ROOT/'REVIEW.json'
    review=read(path) if path.exists() else {}
    causes={'e':'空・単独EOS・文断片','v':'UTF-8不成立','x':'話題が逸れ自然な説明を加えない',
            'u':'文法・語彙が不自然','r':'語句・空白・数字などに有害な反復',
            'c':'文法上の節があるが、自然で適切な新しい一文は成立しない',
            's':'話題に沿う新しい自然な一文','t':'話題に沿うつながった自然な二文',
            'p':'prefixに続く自然なcaption'}
    for i,(n,r) in enumerate(items(name)):
        reason=mapping.get(i)
        if reason is None:
            if r['text'] is None:reason='v'
            elif not r['text'].strip():reason='r' if r['repeat'] and len(r['generated'])>=8 else 'e'
            else:raise ValueError(f'missing rating {i}')
        flags=set(reason)
        assert flags and flags<=causes.keys()
        assert ('p' not in flags or r['panel']=='caption')
        why='。'.join(causes[x] for x in sorted(flags))
        result=review.setdefault(n,{})
        result[r['id']]=dict(reason=why,blind_index=i,clause=bool(flags&set('cst')),
           one=bool(flags&set('st')),two='t'in flags,caption='p'in flags,topic=bool(flags&set('stp')),
           harmful='r' in flags,off_topic='x' in flags,
           harmful_repeat_candidate=r['repeat']['repeatStart'] if 'r'in flags and r['repeat'] else None)
    dump(path,review)

def baseline():
    path=ROOT/'REVIEW.json'
    data=read(path) if path.exists() else {}
    old=read(OLD/'REVIEW.json')['A-985']
    data['A-985']={k:dict(v,clause=False,one=v['one'],two=v['two'],off_topic=False,
                          harmful_repeat_candidate=None) for k,v in old.items()}
    dump(path,data)

if __name__=='__main__':
    op=sys.argv[1]
    if op=='baseline':baseline()
    elif op=='view':print_rows(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else '')
    else:score(sys.argv[2],sys.argv[3:])
