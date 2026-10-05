"""Document-disjoint own byte BPE and continuous raw next-token streams.
No instruction/QA records, pretrained vocabulary, held-text fitting or outside model.
"""
import argparse,array,collections,hashlib,json,pathlib,random,re,sys,time,unicodedata
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'dialogue'))
from tokenizer import SPECIALS,fit_fast,encode_stream
ROOT=pathlib.Path(__file__).resolve().parent

def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def canonical(doc):return doc['site']+':'+unicodedata.normalize('NFKC',doc.get('author','')+'|'+doc['title']).strip()

def split_documents(docs,seed=429):
    """Keep editions/strong exact paragraph overlaps together before fitting."""
    parents=list(range(len(docs)))
    def root(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    def join(a,b):parents[root(b)]=root(a)
    titles={};paragraphs=collections.defaultdict(list);totals=[]
    for i,d in enumerate(docs):
        key=canonical(d)
        if key in titles:join(i,titles[key])
        titles[key]=i
        long={p.strip() for p in d['text'].splitlines() if len(p.strip())>=80};totals.append(len(long))
        for p in long:paragraphs[sha(p.encode())].append(i)
    overlaps=collections.Counter()
    for indices in paragraphs.values():
        for position,a in enumerate(indices):
            for b in indices[position+1:]:overlaps[(a,b)]+=1
    links=[]
    for (a,b),count in sorted(overlaps.items()):
        if count>=2 or count>=.3*min(totals[a],totals[b]):
            join(a,b);links.append(dict(left=docs[a]['id'],right=docs[b]['id'],sharedLongParagraphs=count))
    groups=collections.defaultdict(list)
    for i,d in enumerate(docs):groups[root(i)].append(d)
    sites=collections.defaultdict(list)
    for group in groups.values():
        site=group[0]['site'];assert all(d['site']==site for d in group)
        key=sha((str(seed)+'|'+'|'.join(sorted(d['id'] for d in group))).encode())
        sites[site].append((key,group))
    partitions={};groupids={}
    for site,items in sorted(sites.items()):
        items.sort();n=len(items);held=max(1,round(n*.1));assert n>2*held
        for index,(key,group) in enumerate(items):
            part='test' if index<held else 'validation' if index<2*held else 'train'
            for d in group:partitions[d['id']]=part;groupids[d['id']]=key
    return partitions,groupids,links

def freeze_probes(docs,partitions,part,seed):
    wanted={'aozora':8,'mdn':8,'jma':2,'maff':6} if part=='test' else {'aozora':3,'mdn':3,'jma':1,'maff':2}
    train_texts=[d['text'] for d in docs if partitions[d['id']]=='train']
    result=[]
    for site,n in wanted.items():
        choices=[d for d in docs if d['site']==site and partitions[d['id']]==part]
        choices.sort(key=lambda d:sha((str(seed)+'|probe|'+d['id']).encode()))
        for doc in choices:
            candidates=[p.strip() for p in doc['text'].splitlines() if len(p.strip())>=100 and '。' in p[:180]]
            candidates.sort(key=lambda p:sha((doc['id']+'|'+p).encode()))
            for p in candidates:
                # Whole source paragraph, opening truncated before its first full stop.
                length=28+int(sha(p.encode())[:2],16)%13
                if '。' in p[:length] or len(p)<length+40:continue
                prefix=p[:length]
                if any(prefix in t for t in train_texts):continue
                result.append(dict(id=f'{part}-{site}-{len(result):02d}',document=doc['id'],site=site,url=doc['url'],prefix=prefix,referenceParagraph=p,textSha256=doc['textSha256']))
                break
            if sum(r['site']==site for r in result)>=n:break
    return result

def sample_tokenizer(docs,parts,budget,seed):
    rng=random.Random(seed);by_site=collections.defaultdict(list)
    for doc in docs:
        if parts[doc['id']]=='train':
            for index,paragraph in enumerate(doc['text'].splitlines()):
                if len(paragraph)>=40:by_site[doc['site']].append((doc['id'],index,paragraph))
    selected=[]
    # Equal quota for narrative and combined contemporary explanation; no validation/test strings.
    quotas={'aozora':budget//2,'mdn':budget//3,'jma':budget//12,'maff':budget//12}
    for site,quota in quotas.items():
        candidates=by_site[site];rng.shuffle(candidates);used=0
        for doc,index,p in candidates:
            if used>=quota:break
            selected.append(dict(document=doc,line=index,characters=len(p),sha256=sha(p.encode()),text=p));used+=len(p)
    return selected

def build_streams(docs,parts,tok,out,context=256,lookback=32):
    metadata={};stats={}
    for partition in ['train','validation','test']:
        values=array.array('I');rows=[];info=[];count=0
        for doc in docs:
            if parts[doc['id']]!=partition:continue
            tokens=[SPECIALS['bos']]+encode_stream(doc['text'],tok)+[SPECIALS['eos']]
            offset=len(values);values.extend(tokens);start=0;covered=[]
            while start<len(tokens)-1:
                end=min(start+context+1,len(tokens));prefix=1 if start==0 else lookback
                rows.append(dict(document=doc['id'],site=doc['site'],offset=offset+start,length=end-start,prefixLength=prefix,start=start,end=end))
                covered.extend(tokens[start+prefix:end])
                if end==len(tokens):break
                start=end-lookback
            assert covered==tokens[1:],'Every original target byte and one real EOS counted once'
            assert b''.join(bytes.fromhex(tok['bytes'][t]) for t in covered[:-1])==doc['text'].encode()
            info.append(dict(id=doc['id'],site=doc['site'],offset=offset,length=len(tokens),characters=len(doc['text']),utf8Bytes=len(doc['text'].encode()),textSha256=doc['textSha256']))
            count+=len(tokens)-1
        if sys.byteorder!='little':values.byteswap()
        path=out/f'{partition}.tokens.bin';path.write_bytes(values.tobytes())
        write(out/f'{partition}.index.json',dict(dtype='uint32-little-endian',context=context,lookback=lookback,documents=info,rows=rows,tokensSha256=sha(path.read_bytes())))
        stats[partition]=dict(documents=len(info),windows=len(rows),targetTokens=count,characters=sum(d['characters'] for d in info),utf8Bytes=sum(d['utf8Bytes'] for d in info),bytesPerToken=sum(d['utf8Bytes'] for d in info)/count,tokensSha256=sha(path.read_bytes()))
    return stats

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sample-characters',type=int,default=500000);parser.add_argument('--merges',type=int,nargs='+',default=[2048,4096]);parser.add_argument('--seed',type=int,default=429);args=parser.parse_args()
    source=ROOT/'documents.jsonl';docs=[json.loads(line) for line in source.read_text().splitlines()];source_sha=sha(source.read_bytes())
    assert len({d['id'] for d in docs})==len(docs)
    assert len({d['textSha256'] for d in docs})==len(docs)
    for d in docs:assert d['textSha256']==sha(d['text'].encode())
    parts,groups,links=split_documents(docs,args.seed)
    manifest=dict(schemaVersion=1,sourceSha256=source_sha,seed=args.seed,unit='Entire original document; linked editions and strong long-paragraph overlap stay together',assignments=[dict(document=d['id'],site=d['site'],partition=parts[d['id']],group=groups[d['id']],textSha256=d['textSha256']) for d in docs],overlapLinks=links)
    write(ROOT/'split.json',manifest)
    probes={p:freeze_probes(docs,parts,p,args.seed) for p in ['validation','test']}
    policy=dict(schemaVersion=1,frozenBeforeTokenization=True,seed=args.seed,sourceSha256=source_sha,splitSha256=sha((ROOT/'split.json').read_bytes()),generation=dict(decoding='greedy, unrestricted full vocabulary; no repair/templates/retrieval',maxNewTokens=128,firstSentence='Observe first generated full stop without altering the full token-limited output; quotes/breaks still scored',stopOnEos=True,teacherOrOutsideModel=False),rubric=dict(grammar='0 broken;1 minor errors;2 natural',meaning='0 incoherent;1 partly interpretable;2 meaningful',connection='0 ignores/contradicts prefix;1 weak;2 coherent continuation',repetition='0 loops;1 unnecessary repeat;2 clean',breaks='0 invalid UTF8/control or severe break;1 minor truncation;2 clean sentence closure'),acceptance=dict(minimumTotalScore=9,minimumGrammarScore=2,minimumConnectionScore=2,minimumSentenceSuccessRate=.8,minimumFullOutputNonLoopRate=.9,scope='Each narrative and contemporary-expository subset must pass; no QA/instruction tuning before gate passes.'),selection='Vocabulary/config/checkpoints selected exclusively by validation byte-normalized NLL; test used once after selection.',probes=probes)
    write(ROOT/'generation-policy.json',policy)
    selected=sample_tokenizer(docs,parts,args.sample_characters,args.seed)
    texts=[p['text'] for p in selected]
    sample=dict(seed=args.seed,requestedCharacters=args.sample_characters,characters=sum(len(t) for t in texts),textSha256=sha('\n'.join(texts).encode()),rows=[{k:v for k,v in r.items() if k!='text'} for r in selected],partition='train',externalTokenizer=False)
    write(ROOT/'tokenizer-fit-sample.json',sample)
    print(json.dumps(dict(event='split-frozen',documents=len(docs),groups=len(set(groups.values())),probeCounts={p:len(v) for p,v in probes.items()},sampleCharacters=sample['characters'])),flush=True)
    started=time.time();full=fit_fast(texts,merges=max(args.merges),max_piece_bytes=18)
    assert len(full['merges'])==max(args.merges)
    for merges in sorted(args.merges):
        tok={**full,'bytes':full['bytes'][:262+merges],'merges':full['merges'][:merges]}
        out=ROOT/f'bpe-{merges}';out.mkdir(exist_ok=True);write(out/'tokenizer.json',tok)
        stats=build_streams(docs,parts,tok,out)
        report=dict(sourceSha256=source_sha,splitSha256=sha((ROOT/'split.json').read_bytes()),tokenizerFitSampleSha256=sha((ROOT/'tokenizer-fit-sample.json').read_bytes()),tokenizerSha256=sha((out/'tokenizer.json').read_bytes()),vocabulary=len(tok['bytes']),merges=merges,maxPieceBytes=18,rawNextTokenOnly=True,context=256,lookback=32,stats=stats)
        write(out/'data.json',report);print(json.dumps(dict(event='encoded',merges=merges,elapsedSeconds=round(time.time()-started,2),**stats)),flush=True)
if __name__=='__main__':main()
