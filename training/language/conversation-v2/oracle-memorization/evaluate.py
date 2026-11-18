from experiment import *
from torch.nn.utils.rnn import pad_sequence
ev=read(V/'gv-prose-pilot/EVALUATION_INPUTS.json')
pieces=[bytes.fromhex(x) for x in read(V/'data/tokenizer.json')['bytes']]
spaces=[i for i,p in enumerate(pieces) if p and set(p)=={32}]
def repeat(seq):
    seen={}
    for j in range(len(seq)-3):
        gram=tuple(seq[j:j+4])
        if gram in seen:return dict(first=seen[gram],start=j,completion=j+3,tokens=gram)
        seen[gram]=j
def stats(logits,ref):
    p=logits.double().softmax(-1);v,t=p.topk(5)
    return dict(top5=list(zip(t.tolist(),v.tolist())),p_lf=p[16].item(),p_eos=p[2].item(),p_space=p[spaces].sum().item(),p_ref=p[ref].item() if ref is not None else None,rank_ref=1+int((logits>logits[ref]).sum()) if ref is not None else None)
@torch.inference_mode()
def evaluate(name):
    m=initial(name) if name in plan['models'] else restore(P/'artifacts'/name)[0]
    m.eval();cases=[];calls=0
    for panel,rows in [('prose',ev['prose']),('train',train),('caption',ev['caption'])]:
        if name in ('B-terminal','C-terminal') and panel!='prose':continue
        for r in rows:
            pref=r['prefix']
            gold=r.get('gold',r.get('tokens',[])[len(pref):])
            if panel=='prose':assert gold[:32]==r['teacher_continuation']
            teacher=[]
            if gold:
                end=min(256,len(pref)+len(gold)-1)
                z=m(torch.tensor([(pref+gold)[:end]]))[0,len(pref)-1:]
                calls+=1
                teacher=[stats(a,b) for a,b in zip(z,gold)]
            lengths=plan['oracle'] if name in plan['models'] and panel=='prose' else [0]
            for n in lengths:
                assert n<=len(gold) and 2 not in gold[:n]
                budget=112 if name in plan['models'] and panel=='prose' else (len(gold) if panel=='train' else r['maxNewTokens'])
                cases.append(dict(panel=panel,id=r['id'],prefix=pref,forced=gold[:n],gold=gold[n:],budget=budget,teacher=teacher[n:],generated=[],steps=[]))
    for offset in range(0,len(cases),8):
        group=cases[offset:offset+8]
        while True:
            live=[c for c in group if len(c['generated'])<c['budget'] and c['generated'][-1:]!=[2]]
            if not live:break
            seq=[torch.tensor(c['prefix']+c['forced']+c['generated']) for c in live]
            assert max(map(len,seq))<=256
            z=m(pad_sequence(seq,batch_first=True));calls+=1
            for i,c in enumerate(live):
                j=len(c['generated']);s=stats(z[i,len(seq[i])-1],c['gold'][j] if j<len(c['gold']) else None)
                c['steps'].append(s);c['generated'].append(s['top5'][0][0])
    for c in cases:
        seq=c['generated'];raw=b''.join(pieces[t] for t in seq)
        c.update(raw_hex=raw.hex(),text=raw.decode(errors='replace'),stop='EOS' if seq[-1]==2 else 'budget',repeat=repeat(seq),first_mismatch=next((i for i,(a,b) in enumerate(zip(seq,c['gold'])) if a!=b),None))
        if name in plan['models'] and c['panel']=='prose' and not c['forced']:
            ref=next(x for x in read(V/'gv-prose-pilot/evaluation'/f'{name}.json')['cases'] if x['id']==c['id'])
            assert seq==ref['tokensIncludingEos'][:112]
    (P/f'{name}.json.gz').write_bytes(gzip.compress(json.dumps(dict(forwards=calls,cases=cases),ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
if __name__=='__main__':evaluate(sys.argv[1])
