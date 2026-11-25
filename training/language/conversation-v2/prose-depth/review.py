"""Create a reproducible, model-label-blind review sheet and ingest its decisions."""
import json
import random
import sys

from train import BASE,ROOT,read,dump
from summarize import raw

def sheet(step):
    dev={r['id']:r for r in read(ROOT/'DEV.json')}
    pieces=[bytes.fromhex(x) for x in read(BASE/'data/tokenizer.json')['bytes']]
    records=[]
    for arm in ('A','B'):
        for r in raw(arm,step)['rows']:
            prefix=b''.join(pieces[t] for t in dev[r['id']]['prefix']).decode('utf8')
            records.append((arm,r,prefix))
    random.Random(132000+step).shuffle(records)
    return records

def review(step):
    review_file=ROOT/'REVIEW.json'
    ratings=read(review_file) if review_file.exists() else {}
    names={'r':'有害な反復で内容を展開できない','u':'構文・語彙が不自然',
           'x':'話題に合わない','e':'空・EOSのみ・文断片',
           'p':'prefixに続く自然な短文','s':'話題に沿う自然な新規一文',
           't':'話題に沿う自然な複数文','v':'UTF-8不正で文が成立しない'}
    codes={int(i):c for i,c in (x.split(':') for x in sys.argv[3:])}
    for i,(arm,r,_) in enumerate(sheet(step)):
        code=codes.get(i)
        if code is None:
            if r['text'] is None:
                code='v'
            elif not r['text'].strip():
                code='r' if r['repeat'] and len(r['generated'])>=8 else 'e'
            else:
                raise ValueError(f'Missing reviewed case {i}')
        assert code in names
        result=ratings.setdefault(f'{arm}-{step}',{})
        result[r['id']]=dict(one=code in 'st',two=code=='t',caption=code=='p',
            topic=code in 'pst',harmful=code=='r',reason=names[code],blinded_index=i)
    dump(review_file,ratings)

def view(step):
    for i,(_,r,prefix) in enumerate(sheet(step)):
        text=r['text']
        if text is None or not text.strip():continue
        if r['panel']!='caption' and len(text)>200:
            text=text[:130]+'…'+text[-50:]
        print(i,r['panel'],repr(prefix[-64:]),'→',repr(text),r['stop'])

if __name__=='__main__':
    step=int(sys.argv[2])
    {'view':view,'score':review}[sys.argv[1]](step)
