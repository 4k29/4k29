"""Freeze document-disjoint raw paragraph chains and fresh probes before BPE."""
import array,collections,hashlib,json,pathlib,random,re,sys,unicodedata
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent.parent/'dialogue'))
from tokenizer import fit_fast,encode_stream,SPECIALS
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n')
def chains(doc):
    pending=[];start=0
    for n,line in enumerate(doc['text'].splitlines()):
        p=line.strip();good=bool(p) and len(re.findall(r'[ぁ-ゖァ-ヺ一-龯]',p))/len(p)>=.25 and not re.search(r'お問い合わせ|電話番号|相談電話|^出典[：:]|^資料[：:]|Copyright|All Rights',p,re.I)
        if not good or (not pending and p[-1:] not in '。！？」' and '「' not in p):
            if pending:
                text='\n'.join(pending)
                if text.count('「')==text.count('」') and text.count('（')==text.count('）') and text[-1:] in '。！？」':yield start,n,text
            pending=[];continue
        if not pending:start=n
        pending.append(line);text='\n'.join(pending)
        if len(text)>=512 and text.count('「')==text.count('」') and text.count('（')==text.count('）') and text[-1:] in '。！？」':
            yield start,n+1,text;pending=[]
    if pending:
        text='\n'.join(pending)
        if text.count('「')==text.count('」') and text.count('（')==text.count('）') and text[-1:] in '。！？」':yield start,n+1,text
def main():
    old=[json.loads(x) for x in (ROOT.parent/'round2/documents.jsonl').read_text().splitlines()];added=[json.loads(x) for x in (ROOT/'weather-documents.jsonl').read_text().splitlines()];docs=old+added
    assert len({d['id'] for d in docs})==len(docs)
    parent=list(range(len(docs)));seen={}
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,d in enumerate(docs):
        keys=['title:'+unicodedata.normalize('NFKC',d['site']+'|'+d['author']+'|'+d['title']).strip()]+['paragraph:'+sha(p.strip().encode()) for p in d['text'].splitlines() if len(p.strip())>=80]
        for key in keys:
            if key in seen:parent[find(i)]=find(seen[key])
            seen[key]=i
    groups=collections.defaultdict(list)
    for i,d in enumerate(docs):groups[find(i)].append(d)
    previous={r['document']:r['partition'] for r in read(ROOT.parent/'round2/split.json')['assignments']};parts={};by_site=collections.defaultdict(list);quarantined=[];group_ids={}
    for group in groups.values():
        gid=sha(('1329|'+'|'.join(sorted(d['id'] for d in group))).encode());oldparts={previous[d['id']] for d in group if d['id'] in previous}
        if len(oldparts)>1:part='quarantine';quarantined.append(dict(group=gid,documents=[d['id'] for d in group],priorPartitions=sorted(oldparts)))
        elif oldparts:part='train' if next(iter(oldparts))=='train' else 'development'
        else:part=None;by_site[group[0]['site']].append((gid,group))
        for d in group:
            group_ids[d['id']]=gid
            if part:parts[d['id']]=part
    for site,newgroups in by_site.items():
        ordered=sorted(newgroups);held=max(1,round(len(ordered)*.1))
        assert len(ordered)>held*2
        for i,(_,group) in enumerate(ordered):
            for d in group:parts[d['id']]='test' if i<held else 'validation' if i<held*2 else 'train'
    consumed=set()
    for p in [ROOT.parent/'generation-policy.json',ROOT.parent/'round2/generation-policy.json']:
        consumed.update(r['document'] for rows in read(p)['probes'].values() for r in rows)
    retired=[]
    for site,minimum in [('aozora',8),('mic',6),('env',6)]:
        eligible=sorted([(group_ids[group[0]['id']],group) for group in groups.values() if all(d['site']==site and parts[d['id']]=='train' and d['id'] not in consumed for d in group)])
        held=max(minimum,round(len(eligible)*.1));assert len(eligible)>2*held
        for i,(_,group) in enumerate(eligible[:2*held]):
            for d in group:parts[d['id']]='test' if i<held else 'validation';retired.append(d['id'])
    out=ROOT/'documents.jsonl';out.write_text(''.join(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n' for d in docs))
    split=dict(seed=1329,sourceSha256=sha(out.read_bytes()),quarantinedConflictGroups=quarantined,retiredFromPreviousTrain=retired,previousHeldNowDevelopment=True,randomModelAndTokenizerInitializationRequired=True,previousWeightsNotAllowed=True,assignments=[dict(document=d['id'],site=d['site'],partition=parts[d['id']],group=group_ids[d['id']],textSha256=d['textSha256']) for d in docs]);write(ROOT/'split.json',split)
    train=[d['text'] for d in docs if parts[d['id']]=='train'];probes={}
    for part,counts in [('validation',{'aozora':3,'mic':2,'env':2,'jma':2}),('test',{'aozora':8,'mic':6,'env':6,'jma':4})]:
        result=[]
        for site,count in counts.items():
            options=sorted([d for d in docs if d['site']==site and parts[d['id']]==part and d['id'] not in consumed],key=lambda d:sha(('1329|'+d['id']).encode()))
            for d in options:
                for start,end,text in sorted(chains(d),key=lambda u:sha((d['id']+u[2]).encode())):
                    if len(text)<100 or '。' not in text[:180]:continue
                    n=28+int(sha(text.encode())[:2],16)%13;prefix=text[:n]
                    if '。' in prefix or any(prefix in t for t in train):continue
                    result.append(dict(id=f'{part}-{site}-{len(result):02d}',document=d['id'],site=site,url=d['url'],prefix=prefix,referenceParagraph=text,textSha256=d['textSha256']));break
                if sum(p['site']==site for p in result)>=count:break
            if sum(p['site']==site for p in result)!=count:raise ValueError('Insufficient fresh probes: '+part+' '+site)
        probes[part]=result
    policy=read(ROOT.parent/'round2/generation-policy.json');policy.update(seed=1329,sourceSha256=sha(out.read_bytes()),splitSha256=sha((ROOT/'split.json').read_bytes()),probes=probes,freshTest='Excludes every previously reviewed original/round2 VAL/TEST document and every current TRAIN prefix. New narrative held groups retired from older TRAIN; older weights are exposed and MUST NOT be loaded or treated as an unseen baseline. This round requires fresh random weights and new TRAIN-only tokenizer. Frozen before fitting; no new TEST generation inspected.')
    write(ROOT/'generation-policy.json',policy)
    units=[dict(document=d['id'],site=d['site'],partition=parts[d['id']],startLine=start,endLine=end,text=text,textSha256=sha(text.encode())) for d in docs if parts[d['id']] in ['train','validation','test'] for start,end,text in chains(d)]
    write(ROOT/'units.json',units);rng=random.Random(1329);sample=[]
    for site,quota in [('aozora',400000),('mic',100000),('env',100000),('jma',50000),('mdn',20000),('maff',30000)]:
        items=[u for u in units if u['site']==site and u['partition']=='train'];rng.shuffle(items);used=0
        for unit in items:
            if used>=quota:break
            sample.append(unit);used+=len(unit['text'])
    write(ROOT/'tokenizer-fit-sample.json',dict(seed=1329,trainOnly=True,units=sample,characters=sum(len(u['text']) for u in sample)))
    short=[dict(document=d['id'],line=n,textSha256=sha(p.encode()),characters=len(p)) for d in docs if d['site']=='aozora' for n,p in enumerate(d['text'].splitlines()) if len(p.strip())<40 and '「' in p and p.strip().endswith('」')]
    retained=[q for q in short if any(u['document']==q['document'] and u['startLine']<=q['line']<u['endLine'] for u in units)]
    write(ROOT/'preparation.json',dict(documents=len(docs),sourceCharacters=sum(len(d['text']) for d in docs),addedWeatherDocuments=len(added),parts=dict(collections.Counter(parts.values())),units=dict(collections.Counter(u['partition'] for u in units)),unitsCharacters={p:sum(len(u['text']) for u in units if u['partition']==p) for p in ['train','validation','test']},sourceShortQuotedParagraphs=len(short),retainedShortQuotedParagraphs=len(retained),retainedTrainingShortQuotedParagraphs=sum(parts[q['document']]=='train' for q in retained),quarantineDocuments=sum(p=='quarantine' for p in parts.values()),unitDefinition='Exact consecutive original lines including layout, accumulated until >=512 characters and complete balanced quotes/parentheses; final shorter complete chains retained. No line joining across skipped headings/contact fragments; no synthetic words.'))
    print(json.dumps(dict(event='frozen',documents=len(docs),units=len(units),retainedShortQuotes=len(retained))),flush=True)
    tok=fit_fast([u['text'] for u in sample],merges=8192,max_piece_bytes=18)
    for merges in [4096,8192]:
        vocab={**tok,'merges':tok['merges'][:merges],'bytes':tok['bytes'][:262+merges]};directory=ROOT/f'raw-bpe-{merges}';directory.mkdir(exist_ok=True);write(directory/'tokenizer.json',vocab);stats={}
        for part in ['train','validation','test']:
            values=array.array('I');rows=[];records=[]
            for i,u in enumerate(units):
                if u['partition']!=part:continue
                encoded=[SPECIALS['bos']]+encode_stream(u['text'],vocab)+[SPECIALS['eos']];offset=len(values);values.extend(encoded);start=0;unit=u['document']+':chain:'+str(u['startLine']);covered=[]
                while start<len(encoded)-1:
                    end=min(start+257,len(encoded));prefix=1 if start==0 else 32;rows.append(dict(document=u['document'],unit=unit,site=u['site'],variant=0,offset=offset+start,length=end-start,prefixLength=prefix,start=start,end=end));covered.extend(encoded[start+prefix:end])
                    if end==len(encoded):break
                    start=end-32
                assert covered==encoded[1:];records.append(dict(id=unit,sourceDocument=u['document'],site=u['site'],offset=offset,length=len(encoded),characters=len(u['text']),utf8Bytes=len(u['text'].encode()),textSha256=u['textSha256'],startLine=u['startLine'],endLine=u['endLine']))
            if sys.byteorder!='little':values.byteswap()
            target=directory/f'{part}.tokens.bin';target.write_bytes(values.tobytes());write(directory/f'{part}.index.json',dict(rows=rows,documents=records,tokensSha256=sha(target.read_bytes()),unit='Exact complete consecutive original paragraph chains, literal newlines and original layout. True chain-boundary BOS/EOS, causal overlap32, context256.'))
            stats[part]=dict(units=len(records),windows=len(rows),targetTokens=sum(u['length']-1 for u in records),utf8Bytes=sum(u['utf8Bytes'] for u in records))
        write(directory/'data.json',dict(sourceSha256=sha(out.read_bytes()),splitSha256=sha((ROOT/'split.json').read_bytes()),tokenizerFitSampleSha256=sha((ROOT/'tokenizer-fit-sample.json').read_bytes()),tokenizerSha256=sha((directory/'tokenizer.json').read_bytes()),rawNextTokenOnly=True,externalTokenizer=False,merges=merges,vocabulary=len(vocab['bytes']),stats=stats))
        print(json.dumps(dict(event='encoded',merges=merges,stats=stats)),flush=True)
if __name__=='__main__':main()
