"""Freeze eligible TRAIN seams and collect unmodified C-300 greedy trajectories."""
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
OLD = BASE/'prose-budget-scale'

def read(path):
    return json.loads(path.read_text())

def write(name, obj):
    (ROOT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=1)+'\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def freeze():
    paths = [OLD/name for name in ('TRAIN.json','SCHEDULE.json','REPLAY.json','LEDGER.json',
             'PLAN.json','artifacts/C-600/checkpoint.json')]
    paths += [BASE/'prose-lr-decay/artifacts/C-300/checkpoint.json',BASE/'data/tokenizer.json']
    pieces = list(map(bytes.fromhex,read(paths[-1])['bytes']))
    rows = read(paths[0])
    rng = random.Random(12103)
    order = rng.sample(range(len(rows)),len(rows))
    sites = []
    seen = set()
    groups = set()
    for i in order:
        r = rows[i]
        family = r['family'].split('|')[-1].replace(' ','').casefold()
        if family in seen:
            continue
        prefix = r['prefix']
        raw = b''.join(pieces[t] for t in prefix).decode()
        # Fix the last clause after the first sentence's final comma.
        # The continuation after the period remains exactly the original teacher.
        comma = max(raw.rfind('、'),raw.rfind('，'))
        if comma < 0 or not raw.endswith('。'):
            continue
        cut = len(raw[:comma+1].encode())
        ends = [0]
        for t in prefix:
            ends.append(ends[-1]+len(pieces[t]))
        if cut not in ends:
            continue
        n = ends.index(cut)
        if n<5 or not 3<=len(prefix)-n<=24:
            continue
        seen.add(family)
        groups.add(r['source'])
        sites.append(dict(index=i,id=r['id'],family=family,source=r['source'],prefix=prefix[:n],
                          replaced=prefix[n:],reference=r['gold'],text_sha256=r['text_sha256'],
                          eligible_targets=r['eligible_targets']))
        if len(sites)==30:
            break
    assert len(sites)>=20 and len(groups)>1
    write('SITES.json',sites)
    write('PLAN.json',dict(inherited={str(p.relative_to(BASE)):sha(p) for p in paths},
        sites_sha256=sha(ROOT/'SITES.json'),seed=12103,lengths=[1,4,8,16],optimizer_updates=0,
        seam='Replace only the final clause of the first sentence after its final comma. The original sentence boundary and every gold teacher are fixed.',
        sampling='One frozen PR128 TRAIN passage per normalized family, seeded permutation; eligible last comma on BPE boundary, clause 3–24 tokens.',
        must='Strict UTF8, no special tokens, final sentence period and exactly one clause continuing the original opening; different tokens and text; preserve facts and allow the untouched second sentence naturally.',
        alternate='Punctuation-only Japanese comma to fullwidth comma, with full retokenization and same gold; report separately as a typography inference diagnostic, not as model-derived augmentation.',
        evaluation='No experimental model scores if the candidate review does not support a meaningful history mixture. Reuse PR128 control evidence only.'))
    (ROOT/'PLAN.sha256').write_text(sha(ROOT/'PLAN.json')+'\n')

def generate():
    sys.path.insert(0,str(OLD))
    from run_budget import start, parent, torch
    from verify_budget import recover
    plan = read(ROOT/'PLAN.json')
    assert sha(ROOT/'PLAN.json')==(ROOT/'PLAN.sha256').read_text().strip()
    assert sha(ROOT/'SITES.json')==plan['sites_sha256']
    for p,h in plan['inherited'].items():
        assert sha(BASE/p)==h
    states=[]
    for folder in (parent,OLD/'artifacts/C-600'):
        state=recover(folder)
        states.append(dict(step=state['uniqueUpdates'],history=len(state['history']),
            adam_steps=sorted({int(v['step']) for v in state['optimizer']['state'].values()}),
            checkpoint_sha256=read(folder/'checkpoint.json')['sha256']))
    model,_,_ = start(parent)
    model.eval()
    pieces = list(map(bytes.fromhex,read(BASE/'data/tokenizer.json')['bytes']))
    results=[]
    calls=0
    with torch.inference_mode():
        for site in read(ROOT/'SITES.json'):
            tokens=[]
            scores=[]
            for _ in range(16):
                logits=model(torch.tensor([site['prefix']+tokens]))[0,-1]
                calls+=1
                token=int(logits.argmax())
                tokens.append(token)
                scores.append(float(logits.double().softmax(0)[token]))
                if token==2:
                    break
            candidates=[]
            for n in plan['lengths']:
                selected=tokens[:n]
                raw=b''.join(pieces[t] for t in selected)
                try:
                    decoded=raw.decode()
                except UnicodeDecodeError:
                    decoded=None
                if len(selected)<n:
                    rule='eos_before_requested_length'
                elif set(selected)&set(range(6)):
                    rule='special_token'
                elif decoded is None:
                    rule='invalid_utf8'
                elif selected==site['replaced'] or raw==b''.join(pieces[t] for t in site['replaced']):
                    rule='identical_surface'
                elif not decoded.endswith('。') or decoded.count('。')!=1 or '\n' in decoded:
                    rule='not_complete_single_clause'
                else:
                    rule='requires_semantic_review'
                candidates.append(dict(length=n,tokens=selected,raw_hex=raw.hex(),text=decoded,rule=rule))
            results.append(dict(id=site['id'],generated=tokens,p_greedy=scores,
                stop='EOS' if tokens[-1]==2 else 'budget',candidates=candidates))
    write('CANDIDATES.json',dict(checkpoints=states,forwards=calls,optimizer_calls=0,results=results))

if __name__=='__main__':
    if sys.argv[1]=='freeze':
        freeze()
    else:
        generate()
