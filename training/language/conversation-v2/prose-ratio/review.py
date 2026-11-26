"""Render anonymous complete continuations and record explicit case-level scores."""
import gzip
import json
import random
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREV=ROOT.parent/'prose-development'
DEPTH=ROOT.parent/'prose-depth'

def read(path):
    data=path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix=='.gz' else data)

def cases(label):
    if label=='start':
        rows=read(DEPTH/'A-985-eval.json.gz')['rows']
        scores=read(DEPTH/'A-985-extra.json')['scores']
        for row in rows:
            if row['panel']=='independent':row['panel']='depth24'
            if row['id'] in scores:
                gold=scores[row['id']]
                row.update({k:gold[k] for k in ('ref','gold','first')})
                for i,v in gold['self_logp'].items():row['steps'][int(i)]['ref']=v
        return rows+read(PREV/'monitor-985.json.gz')['rows']+read(PREV/'holdout-985.json.gz')['rows']
    if label.startswith('A-'):
        rows=read(PREV/f'{label}.json.gz')['rows']
        if label=='A-1967':rows+=read(PREV/'holdout-1967.json.gz')['rows']
        if label=='A-2950':rows+=read(ROOT/'A-2950-regression34.json.gz')['rows']
        return rows
    return read(ROOT/f'{label}.json.gz')['rows']

def hidden(names):
    rows=[(state,r) for state in names.split(',') for r in cases(state) if r['panel']!='train']
    random.Random('ratio-review-v1:'+names).shuffle(rows)
    return rows

def view(names,panel,begin,end):
    dev={r['id']:r for r in read(ROOT/'DEV.json')}
    pieces=list(map(bytes.fromhex,read(ROOT.parent/'data/tokenizer.json')['bytes']))
    for i,(_,r) in enumerate(hidden(names)):
        if not begin<=i<end or (panel=='caption')!=(r['panel']=='caption'):
            continue
        prefix=b''.join(pieces[t] for t in dev[r['id']]['prefix']).decode(errors='replace')
        if r['text'] is None or not r['text'].strip():
            continue
        print(i,repr(prefix if panel=='caption' else prefix[-110:]), repr(r['text']),r['stop'])

FLAGS={'u':'語法・語彙の崩れまたは未完の断片','r':'内容を損なう語句・数字・空白などの反復',
       'x':'元の話題に無関係な内容','k':'話題に関連する語句・節を維持','c':'成立する節はあるが自然で話題に沿う新規一文はない',
       's':'自然で話題に沿う新規一文','t':'自然で意味がつながる新規二文','p':'prefix込みで自然な補完',
       'e':'空の出力または短い空白だけで終了','v':'UTF-8不成立'}

def record(names,values):
    path=ROOT/'REVIEW.json'
    data=read(path) if path.exists() else {}
    ratings={int(k):v for k,v in (d.split(':',1) for d in values)}
    for i,(label,row) in enumerate(hidden(names)):
        rating=ratings.get(i)
        if rating is None:
            if row['text'] is None:rating='v'
            elif not row['text'].strip():rating='r' if row['repeat'] else 'e'
            elif row['id'] not in data.get(label,{}):continue
            else:continue
        reasons=set(rating)
        assert reasons and reasons<=FLAGS.keys()
        assert ('p' not in reasons or row['panel']=='caption')
        data.setdefault(label,{})[row['id']]=dict(blind_index=i,reason='。'.join(FLAGS[x] for x in sorted(reasons)),
            one=bool(reasons&{'s','t'}),two='t'in reasons,clause=bool(reasons&{'c','s','t'}),
            natural_end=row['stop']=='EOS' and bool(reasons&{'p','s','t'}) and 'r' not in reasons,
            topic=bool(reasons&{'k','p','s','t'}),harmful='r'in reasons,off_topic='x'in reasons,caption='p'in reasons,
            repeat_candidate=row['repeat']['repeatStart'] if 'r'in reasons and row['repeat'] else None)
    path.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True)+'\n')

if __name__=='__main__':
    op,names,*args=sys.argv[1:]
    if op=='view':view(names,args[0],int(args[1]),int(args[2]))
    else:record(names,args)
