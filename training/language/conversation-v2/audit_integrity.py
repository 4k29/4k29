"""Final data-only integrity audit. Does not import a model or optimizer."""
import argparse,array,ast,collections,hashlib,importlib.util,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2]
RAW=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train')
def read(p):return json.loads(p.read_text())
def sha(p):
    d=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):d.update(b)
    return d.hexdigest()
def main(a):
    a.data=a.data.resolve();a.output=a.output.resolve()
    base=a.data.parent;data=read(a.data);split=read(base/'split.json');tok=read(ROOT/data['tokenizerPath'])
    assert sha(base/'split.json')==data['splitSha256']
    source={}
    for name in ['sources/documents.jsonl','added-human-source/documents.jsonl']:
        p=ROOT/'training/language/round46'/name
        for line in p.open():
            d=json.loads(line)
            if d['originalDocument'].startswith('realpersona:'):
                assert d['partition']=='train'and d['license']=='CC-BY-SA-4.0';source[d['originalDocument']]=d
    assert len(source)==len(split['rows'])==8975
    splitrows={x['id']:x for x in split['rows']};receipts=[];all_raw_turns=0
    for ident,d in sorted(source.items()):
        p=RAW/(ident.split(':')[1]+'.json');raw=read(p);h=sha(p)
        assert h==d['sourceSha256']==splitrows[ident]['sourceSha256']
        assert '\n'.join(u['text']for u in raw['utterances'])==d['text']
        assert splitrows[ident]['speakers']==raw['interlocutors']
        assert all(u['utterance_id']==j for j,u in enumerate(raw['utterances']))
        receipts.append({'path':str(p),'sha256':h});all_raw_turns+=len(raw['utterances'])
    digest=hashlib.sha256(json.dumps(receipts,separators=(',',':')).encode()).hexdigest()
    assert digest==data['originalTrainSourceReceiptsDigest']and all_raw_turns==269877
    parts={name:[json.loads(s)for s in (base/(name+'.docs.jsonl')).read_text().splitlines()]for name in ['train','dev']}
    ids={name:{d['id']for d in docs}for name,docs in parts.items()}
    assert not ids['train']&ids['dev']
    assert ids['train']=={x['id']for x in split['rows']if x['partition']=='train'}
    assert ids['dev']=={x['id']for x in split['rows']if x['partition']=='dev'}
    assert not ids['dev']&set(split['exposedDocumentsExcludedFromDev'])
    assert set(tok['fitSubset']['documents'])<=ids['train']and not set(tok['fitSubset']['documents'])&ids['dev']
    chars={c for d in parts['train']for u in d['utterances']for c in u['text']}
    assert set(tok['glyphTokenIds'])==chars and tok['trainingCharacterTypes']==len(chars)
    assert tok['trainingCharacters']==sum(len(u['text'])for d in parts['train']for u in d['utterances'])
    assert all(tok['bytes'][i]==''for i in range(6))and tok['bytes'][6:262]==[bytes([i]).hex()for i in range(256)]
    for name,docs in parts.items():
        for d in docs:
            original=read(RAW/(d['id'].split(':')[1]+'.json'))['utterances']
            assert len(original)==len(d['utterances'])
            for j,(u,v) in enumerate(zip(d['utterances'],original)):
                assert u['ordinal']==u['originalUtteranceId']==v['utterance_id']==j
                assert u['text']==v['text']and u['speakerId']==v['interlocutor_id']
    speakers={name:{s for d in docs for s in d['speakers']}for name,docs in parts.items()}
    fam={name:{d['normalizedDocumentFamily']for d in docs}for name,docs in parts.items()}
    assert not speakers['train']&speakers['dev']and not fam['train']&fam['dev']
    values=array.array('I');values.frombytes((ROOT/data['trainTokensPath']).read_bytes())
    if sys.byteorder!='little':values.byteswap()
    docs_byid={d['id']:d for d in parts['train']};doc_start={};pos=0
    for d in parts['train']:
        # True source length is recoverable from explicit special boundaries;
        # prepared-data audit separately reconstructs every exact BPE body.
        assert values[pos]==1;doc_start[d['id']]=pos;end=pos+1
        while end<len(values)and values[end]!=1:end+=1
        expected_turns=len(d['utterances']);assert values[pos:end].count(2)==expected_turns
        pos=end
    assert pos==len(values)
    coverage=array.array('B',[0])*len(values);eos_targets=0;targets=0
    for r in data['trainWindows']:
        start=r['offset'];length=r['length'];ident=r['document']
        assert start==doc_start[ident]+r['startToken']and 2<=length<=257
        assert all(t!=1 for t in values[start+1:start+length]),'Window must not cross another document BOS'
        for j in range(start+1,start+length):
            assert coverage[j]==0,'Target repeated across training windows';coverage[j]+=1;targets+=1
            eos_targets+=values[j]==2
    assert all(c==(0 if t==1 else 1)for c,t in zip(coverage,values))
    assert eos_targets==180006 and targets==len(values)-len(parts['train'])
    # Exercise the actual trainer's packing function for every window without
    # constructing a model, optimizer or random tensor.
    spec=importlib.util.spec_from_file_location('_v2_integrity_core',H/'core.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    import numpy as np
    mapped=np.asarray(values,dtype=np.uint32);windows=data['trainWindows'];padpositions=0
    for first in range(0,len(windows),64):
        indices=list(range(first,min(first+64,len(windows))))
        x,y,stats=core.pack(mapped,windows,indices,len(tok['bytes']))
        assert int(y.ne(-100).sum())==sum(windows[i]['length']-1 for i in indices)
        for batch,i in enumerate(indices):
            n=windows[i]['length']-1;offset=windows[i]['offset']
            assert x[batch,:n].tolist()==list(values[offset:offset+n])
            assert y[batch,:n].tolist()==list(values[offset+1:offset+n+1])
            assert bool(x[batch,n:].eq(0).all())and bool(y[batch,n:].eq(-100).all())
            padpositions+=256-n
    train_source=H/'train.py';core_source=H/'core.py';training_isolation={}
    for p in [train_source,core_source]:
        tree=ast.parse(p.read_text());literals={n.value for n in ast.walk(tree)if isinstance(n,ast.Constant)and isinstance(n.value,str)}
        assert not {'goldTokens','targetText','benchmark-dev.json'}&literals
        training_isolation[p.name]={'sha256':sha(p),'noBenchmarkGoldOrTextLiteralReferences':True}
    assert "open_tokens(data, 'train')"in train_source.read_text()
    allsha={str(p.relative_to(H)):sha(p)for p in sorted(base.rglob('*'))if p.is_file()and p!=a.output}
    for rel,h in data['codeReceipts'].items():assert sha(ROOT/rel)==h
    for x in data['sourceReceipts']:
        p=pathlib.Path(x['path']);p=p if p.is_absolute()else ROOT/p
        assert sha(p)==x['sha256']
    prepared=read(base/'prepared-data-audit.json');assert prepared['status']=='PASS'
    result={'status':'PASS','scope':'All original source SHA, data/feature/glyph/BPE separation, window/EOS coverage; no model imported',
        'optimizerUpdates':0,'sealedTestRead':False,'rawOriginalTrainDocumentsShaVerified':len(source),'rawOriginalUtterances':all_raw_turns,
        'trainTargetPositionsExactlyOnce':targets,'trainFirstBosPositionsExcluded':len(parts['train']),
        'trueTurnEosTargetsExactlyOnce':eos_targets,'padTargetsScored':0,'actualTrainerPackAllWindowsVerified':len(windows),'maskedPadPositions':padpositions,'noDocumentBoundaryCrossing':True,
        'persistentSpeakerSplitDisjoint':True,'normalizedWholeDocumentFamiliesDisjoint':True,'tokenizerGlyphInventoryTrainOnly':True,
        'wordBpeFitDocumentsTrainOnly':len(tok['fitSubset']['documents']),'wordBpeFitCharacters':tok['fitSubset']['characters'],
        'trainingGoldIsolationStaticReview':training_isolation,'staticReviewLimit':'Literal-reference checks accompany manual source review; they are not a general proof of noninterference.',
        'manualTrainingIsolationReview':'train.run opens only train token memmap/windows for model updates; validate reads manifest and tokenizer only. core.pack reads only supplied windows; neither reads benchmark gold or DEV target arrays for updates. Decoder source imports no data files.',
        'allPreparedArtifactsSha256':allsha,'dataSha256':sha(a.data),'exactBenchmarkHistoryGoldTrainOverlapCases':prepared['benchmarkExactFullExampleOverlapCases'],
        'exactBenchmarkGoldOnlyTrainOverlapCases':prepared['benchmarkExactGoldOverlapCases'],
        'limits':['No claim of latent semantic-family independence','Old R46 trained these original TRAIN documents; holdout is fresh only for this new scratch-series weights/tokenizer','Natural short phrases can legitimately recur; exact gold-only overlap is not full-example memorization']}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['allPreparedArtifactsSha256','trainingGoldIsolationStaticReview']},ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);main(p.parse_args())
