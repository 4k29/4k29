"""Freeze new document groups and unseen openings before own BPE fitting."""
import collections, importlib.util, json, pathlib, random, sys
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent));sys.path.insert(0,str(ROOT.parent.parent/'dialogue'))
spec=importlib.util.spec_from_file_location('original_prepare',ROOT.parent/'prepare.py'); base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from tokenizer import fit_fast, SPECIALS

def split_modern(docs):
    """Even ONE exact paragraph >=80 chars links government editions."""
    parent=list(range(len(docs)));seen={};links=[]
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,d in enumerate(docs):
        keys=[('title',base.canonical(d))]+[('paragraph',base.sha(p.encode())) for p in d['text'].splitlines() if len(p)>=80]
        for key in keys:
            if key in seen:
                j=seen[key];parent[find(i)]=find(j);links.append(dict(left=d['id'],right=docs[j]['id'],kind=key[0],shaOrTitle=key[1]))
            seen[key]=i
    bysite=collections.defaultdict(dict)
    for i,d in enumerate(docs):bysite[d['site']].setdefault(find(i),[]).append(d)
    parts={};groups={}
    for site,values in sorted(bysite.items()):
        rows=sorted((base.sha(('829|'+'|'.join(sorted(d['id'] for d in group))).encode()),group) for group in values.values())
        held=max(1,round(len(rows)*.1));assert len(rows)>2*held
        for index,(key,group) in enumerate(rows):
            part='test' if index<held else 'validation' if index<2*held else 'train'
            for d in group:parts[d['id']]=part;groups[d['id']]=key
    return parts,groups,links

def main():
    old=[json.loads(x) for x in (ROOT.parent/'documents.jsonl').read_text().splitlines()]
    modern=[json.loads(x) for x in (ROOT/'modern-documents.jsonl').read_text().splitlines()]
    oldparts={d['document']:d for d in base.json.loads((ROOT.parent/'split.json').read_text())['assignments']}
    # Preserve every old assignment, including consumed TEST as development data.
    parts,groups,links=split_modern(modern)
    for d in old: parts[d['id']]=oldparts[d['id']]['partition'];groups[d['id']]=oldparts[d['id']]['group']
    docs=old+modern; path=ROOT/'documents.jsonl';path.write_text(''.join(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n' for d in docs))
    source_sha=base.sha(path.read_bytes())
    split=dict(seed=829,sourceSha256=source_sha,oldAssignmentsPreserved=True,overlapLinks=links,assignments=[dict(document=d['id'],site=d['site'],partition=parts[d['id']],group=groups[d['id']],textSha256=d['textSha256']) for d in docs])
    base.write(ROOT/'split.json',split)
    previous=json.loads((ROOT.parent/'generation-policy.json').read_text())
    consumed={r['document'] for rows in previous['probes'].values() for r in rows}
    train=[d['text'] for d in docs if parts[d['id']]=='train'];probes={}
    for part in ['validation','test']:
        result=[]
        for site,count in [('aozora',3 if part=='validation' else 8),('mic',3 if part=='validation' else 8),('env',3 if part=='validation' else 8)]:
            choices=sorted([d for d in docs if d['site']==site and parts[d['id']]==part and d['id'] not in consumed],key=lambda d:base.sha((str(829)+d['id']).encode()))
            for d in choices:
                candidates=sorted([p for p in d['text'].splitlines() if len(p)>=100 and '。' in p[:180]],key=lambda p:base.sha((d['id']+p).encode()))
                for p in candidates:
                    n=28+int(base.sha(p.encode())[:2],16)%13; prefix=p[:n]
                    if '。' in prefix or len(p)<n+40 or any(prefix in t for t in train): continue
                    result.append(dict(id=f'{part}-{site}-{len(result):02d}',document=d['id'],site=site,url=d['url'],prefix=prefix,referenceParagraph=p,textSha256=d['textSha256']));break
                if sum(r['site']==site for r in result)>=count:break
            if sum(r['site']==site for r in result)!=count:raise ValueError('Insufficient fresh probes: '+part+' '+site)
        probes[part]=result
    policy={**previous,'seed':829,'sourceSha256':source_sha,'splitSha256':base.sha((ROOT/'split.json').read_bytes()),'probes':probes,'freshTest':'All probe documents exclude both original TEST22 and VAL9; modern sources not used by any parent. New model initialized randomly. Old TEST22 development only.'}
    base.write(ROOT/'generation-policy.json',policy)
    # Cross-partition exact long-paragraph overlaps are reported, never concealed.
    paragraphs=collections.defaultdict(set)
    for d in docs:
        for p in d['text'].splitlines():
            if len(p)>=80:paragraphs[base.sha(p.encode())].add(parts[d['id']])
    base.write(ROOT/'overlap-audit.json',dict(crossPartitionParagraphs=[dict(sha256=k,partitions=sorted(v)) for k,v in paragraphs.items() if len(v)>1],allProbePrefixesAbsentTrain=True))
    candidates=collections.defaultdict(list)
    for d in docs:
        if parts[d['id']]=='train':
            for line,p in enumerate(d['text'].splitlines()):
                if len(p)>=40:candidates[d['site']].append(dict(document=d['id'],line=line,text=p,sha256=base.sha(p.encode()),characters=len(p)))
    rng=random.Random(829);sample=[]
    for site,quota in [('aozora',200000),('mic',200000),('env',200000),('mdn',80000),('jma',10000),('maff',10000)]:
        items=candidates[site];rng.shuffle(items);used=0
        for p in items:
            if used>=quota:break
            sample.append(p);used+=len(p['text'])
    base.write(ROOT/'tokenizer-fit-sample.json',dict(seed=829,trainOnly=True,characters=sum(p['characters'] for p in sample),paragraphs=sample))
    print(json.dumps(dict(event='frozen',documents=len(docs),characters=sum(len(d['text']) for d in docs),probes={k:len(v) for k,v in probes.items()})),flush=True)
    fitted=fit_fast([p['text'] for p in sample],merges=8192,max_piece_bytes=18)
    for merges in [4096,8192]:
        tok={**fitted,'merges':fitted['merges'][:merges],'bytes':fitted['bytes'][:262+merges]}
        out=ROOT/f'bpe-{merges}';out.mkdir(exist_ok=True);base.write(out/'tokenizer.json',tok)
        stats=base.build_streams(docs,parts,tok,out)
        base.write(out/'data.json',dict(sourceSha256=source_sha,splitSha256=base.sha((ROOT/'split.json').read_bytes()),tokenizerFitSampleSha256=base.sha((ROOT/'tokenizer-fit-sample.json').read_bytes()),tokenizerSha256=base.sha((out/'tokenizer.json').read_bytes()),vocabulary=len(tok['bytes']),merges=merges,maxPieceBytes=18,rawNextTokenOnly=True,context=256,lookback=32,stats=stats))
        print(json.dumps(dict(event='encoded',merges=merges,stats=stats)),flush=True)

if __name__=='__main__':main()
