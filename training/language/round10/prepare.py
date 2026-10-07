"""Freeze expanded raw folds and probes before extending the own vocabulary."""
import collections,hashlib,importlib.util,json,pathlib,unicodedata
ROOT=pathlib.Path(__file__).resolve().parent;OLD=ROOT.parent/'round8';ADDED=ROOT.parent/'round9-source';CHAIN=ROOT.parent/'round3'
spec=importlib.util.spec_from_file_location('own_chain_definition',CHAIN/'prepare.py');original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashtext(t):return hashlib.sha256(t.encode()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n')
def main():
    if (ROOT/'split.json').exists():raise ValueError('Frozen fold already exists; use a new experiment')
    old=[json.loads(x) for x in (OLD/'documents.jsonl').read_text().splitlines()];new=[json.loads(x) for x in (ADDED/'documents.jsonl').read_text().splitlines()];docs=old+new
    assert len({d['id'] for d in docs})==len(docs)
    previous={r['document']:r['partition'] for r in read(OLD/'split.json')['assignments']}
    parents={d['id']:d['id'] for d in docs};seen={}
    def find(x):
        while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
        return x
    for d in docs:
        keys=['title:'+unicodedata.normalize('NFKC',d['site']+'|'+d['author']+'|'+d['title']).strip()]+['paragraph:'+hashtext(p.strip()) for p in d['text'].splitlines() if len(p.strip())>=80]
        for key in keys:
            if key in seen:
                a,b=find(d['id']),find(seen[key]);parents[max(a,b)]=min(a,b)
            seen[key]=d['id']
    groups=collections.defaultdict(list)
    for d in docs:groups[find(d['id'])].append(d)
    parts={};groupids={};pending=[];forced=[]
    for group in groups.values():
        gid=hashtext('1929|'+'|'.join(sorted(d['id'] for d in group)));prior={previous[d['id']] for d in group if d['id'] in previous}
        if len(prior)>1:raise ValueError('New source bridges old partitions; isolate before warm starting')
        if prior:
            part=next(iter(prior))
            for d in group:parts[d['id']]=part
            if any(d['id'] not in previous for d in group):forced.append(dict(group=gid,partition=part,documents=[d['id'] for d in group]))
        else:pending.append((gid,group))
        for d in group:groupids[d['id']]=gid
    held=max(1,round(len(pending)*.075));assert len(pending)>2*held
    for i,(_,group) in enumerate(sorted(pending)):
        for d in group:parts[d['id']]='test' if i<held else 'validation' if i<held*2 else 'train'
    assert all(parts[k]==v for k,v in previous.items())
    source=ROOT/'documents.jsonl';source.write_text(''.join(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n' for d in docs))
    write(ROOT/'split.json',dict(seed=1929,sourceSha256=sha(source),parentSourceSha256=sha(OLD/'documents.jsonl'),parentSplitSha256=sha(OLD/'split.json'),addedSourceSha256=sha(ADDED/'documents.jsonl'),allParentAssignmentsPreserved=True,onlyNewUnexposedGroupsEligibleForNewHeld=True,forcedPriorConnections=forced,assignments=[dict(document=d['id'],site=d['site'],partition=parts[d['id']],group=groupids[d['id']],textSha256=d['textSha256']) for d in docs]))
    oldunits=read(OLD/'units.json');units=oldunits+[dict(document=d['id'],site=d['site'],partition=parts[d['id']],startLine=a,endLine=b,text=t,textSha256=hashtext(t)) for d in new if parts[d['id']] in ['train','validation','test'] for a,b,t in original.chains(d)]
    write(ROOT/'units.json',units)
    policy=read(OLD/'generation-policy.json');train=[u['text'] for u in units if u['partition']=='train']
    for part in ['validation','test']:
        for site in ['stat','bunka']:
            probes=[]
            for d in sorted((d for d in new if parts[d['id']]==part and d['site']==site),key=lambda d:hashtext('1929|'+d['id'])):
                for a,b,text in sorted(original.chains(d),key=lambda t:hashtext(d['id']+t[2])):
                    if len(text)<100 or '。' not in text[:180]:continue
                    prefix=text[:28+int(hashtext(text)[:2],16)%13]
                    if '。' in prefix or any(prefix in t for t in train):continue
                    probes.append(dict(id=f'{part}-{site}-new-{len(probes):02d}',document=d['id'],site=site,url=d['url'],prefix=prefix,referenceParagraph=text,textSha256=d['textSha256']));break
                if len(probes)==2:break
            assert len(probes)==2
            policy['probes'][part]+=probes
    for rows in policy['probes'].values():
        for p in rows:assert not any(p['prefix'] in text for text in train)
    policy.update(seed=1929,sourceSha256=sha(source),splitSha256=sha(ROOT/'split.json'),frozenBeforeThisTraining=True,frozenBeforeVocabularyExtension=True,parentFoldPreserved=True,freshAddedHeld='New statistical/cultural groups only, disjoint from every parent exposed group; all prior TEST continuations remain unopened.',comparison=dict(baseline='Same own8-layer model and TRAIN-only glyph+word BPE representation before child updates; parent glyph rows retained and word rows initialized from own glyph means',candidate='Same architecture/vocabulary/fold after actual10000 child updates; vocabulary size and checkpoint chosen only by canonical VAL NLL/byte',oldCoreValidationGateAlsoRequired=True,parent13ValidationGateAlsoRequired=True,externalWeightsOrTeacherForbidden=True,testGatedByDevelopmentLanguageReview=True))
    policy['generation']['representation']='Own TRAIN glyph assembly followed by short word BPE; no outside vocabulary. Max192 new tokens may represent more characters than the prior character model; compare initialization versus trained weights within each representation. All vocabulary is allowed, no output repair.'
    write(ROOT/'generation-policy.json',policy)
    write(ROOT/'corpus-preparation.json',dict(preparerSourceSha256=sha(pathlib.Path(__file__)),chainDefinitionSourceSha256=sha(CHAIN/'prepare.py'),documents=len(docs),newDocuments=len(new),parts=dict(collections.Counter(parts.values())),newParts=dict(collections.Counter(parts[d['id']] for d in new)),units=dict(collections.Counter(u['partition'] for u in units)),unitCharacters={p:sum(len(u['text']) for u in units if u['partition']==p) for p in ['train','validation','test']},oldUnitsPreservedExactly=True,policyFrozenBeforeVocabularyFit=True,optimizerUpdates=0,externalWeights=False,externalTokenizer=False,externalInferenceAPI=False,wikipedia=False))
    print(json.dumps(dict(documents=len(docs),newDocuments=len(new),parts=dict(collections.Counter(parts.values())),units=len(units),vocabularyNotFitted=True,optimizerUpdates=0)),flush=True)
if __name__=='__main__':main()
