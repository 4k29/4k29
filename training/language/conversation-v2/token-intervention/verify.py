"""Validate artifact integrity, replay argmax and report counts without optimizer or model loading."""
import gzip
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

P=Path(__file__).resolve().parent
V=P.parent
def digest(path):
    return sha256(path.read_bytes()).hexdigest()
plan=json.loads((P/'PLAN.json').read_text())
assert digest(P/'PLAN.json')==(P/'PLAN.sha256').read_text().strip()
archive=V/'gv-collapse-diagnostic/DIAGNOSTIC.json.gz'
assert digest(archive)==plan['archive_SHA']
assert digest(V/'gv-prose-pilot/EVALUATION_INPUTS.json')==plan['inputs_SHA']
oldplan=json.loads((V/'gv-collapse-diagnostic/PLAN.json').read_text())
for rel,h in oldplan['inputs'].items():
    assert digest(V/rel)==h
for ref in plan['models'].values():
    path=V/ref['path']
    manifest=json.loads(path.read_text())
    h=sha256()
    for part in manifest['chunks']:
        data=(path.parent/part['path']).read_bytes()
        assert sha256(data).hexdigest()==part['sha256']
        h.update(data)
    assert h.hexdigest()==manifest['sha256']==ref['sha']
base={(r['model'],r['id']):r for r in json.load(gzip.open(archive))['cases']}
result=json.load(gzip.open(P/'RESULTS.json.gz'))
rows=result['cases']
key=lambda x:(x['model'],x['id'],x['arm'])
bykey={key(r):r for r in rows}
assert set(bykey)=={key(e) for e in plan['selection'] if e['rank']}
assert len(rows)==len(bykey) and result['optimizer_calls']==0
pieces=[bytes.fromhex(s) for s in json.loads((V/'data/tokenizer.json').read_text())['bytes']]
for e in plan['selection']:
    if not e['rank']:continue
    r=bykey[key(e)]
    x=base[e['model'],e['id']]
    j=e['j']
    seq=r['tokens']
    assert seq[:j]==x['generated'][:j] and seq[j]==e['token']!=x['generated'][j]
    assert e['top10'][e['rank']-1]==[seq[j],e['p']]
    assert r['replay_argmax']==seq[:j]+[x['generated'][j]]+seq[j+1:]
    assert seq[j+1:]==[s['t'] for s in r['steps']]
    assert b''.join(pieces[t] for t in seq).hex()==r['raw_hex']
    assert len(x['prefix'])+len(seq)-1<=256 and (seq[-1]==2 or len(seq)==128)
    assert r['forwards']==len(seq)-j
    seen=set()
    start=None
    for k in range(len(seq)-3):
        gram=tuple(seq[k:k+4])
        if k>j and gram in seen:
            start=k
            break
        seen.add(gram)
    assert start==(r['recurrence']['start'] if r['recurrence'] else None)
assert result['forwards']==sum(r['forwards'] for r in rows)
def table():
    lines=['|状態|条件|全入力|実施|4-gram再出現|再出現距離中央値|EOS|持続回復|','|---|---|---:|---:|---:|---:|---:|---:|']
    reviews=json.loads((P/'REVIEW.json').read_text())
    assert len(reviews)==len(rows) and {key(r) for r in reviews}==set(bykey)
    for name in plan['models']:
        orig=[r for (n,i),r in base.items() if n==name]
        lines.append(f"|{name}|A|18|18|{sum(bool(r['repeat']) for r in orig)}|—|{sum(r['generated'][-1]==2 for r in orig)}|0|")
        for arm in ('B','C'):
            subset=[r for r in rows if r['model']==name and r['arm']==arm]
            distances=[r['recurrence']['distance'] for r in subset if r['recurrence']]
            successes=sum(r['success'] for r in reviews if r['model']==name and r['arm']==arm)
            lines.append(f"|{name}|{arm}|18|{len(subset)}|{len(distances)}|{median(distances) if distances else '—'}|{sum(r['stop']=='EOS' for r in subset)}|{successes}|")
    return '\n'.join(lines)+'\n'
if __name__=='__main__':
    assert (P/'TABLES.md').read_text()==table()
    print('PASS',len(base),len(rows),result['forwards'])
