"""Read-only checks of all fresh data streams, true turn boundaries and overlap."""
import argparse,array,collections,hashlib,json,pathlib,sys,unicodedata
from new_tokenizer import Encoder
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def nrm(s):return ''.join(unicodedata.normalize('NFKC',s).split())
def signature(texts):return hashlib.sha256(json.dumps(texts,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def main(a):
    data=read(a.data);tok=read(ROOT/data['tokenizerPath']);enc=Encoder(tok)
    assert sha(ROOT/data['tokenizerPath'])==data['tokenizerSha256']
    base=a.data.parent;docs={p:[json.loads(s)for s in (base/(p+'.docs.jsonl')).read_text().splitlines()]for p in ['train','dev']}
    train_chars={c for d in docs['train']for u in d['utterances']for c in u['text']}
    assert train_chars==set(tok['glyphTokenIds'])
    families=[d['normalizedDocumentFamily']for p in docs for d in docs[p]];assert len(families)==len(set(families))
    assert not {s for d in docs['train']for s in d['speakers']}&{s for d in docs['dev']for s in d['speakers']}
    streamstats={};expected_windows={}
    for p in docs:
        path=ROOT/data[p+'TokensPath'];assert sha(path)==data[p+'TokensSha256']
        values=array.array('I');values.frombytes(path.read_bytes())
        if sys.byteorder!='little':values.byteswap()
        offset=0;allrows={};turns=0;body=0;roles=0
        for d in docs[p]:
            expected=[1]
            for u in d['utterances']:
                ids=enc(u['text']);expected.extend([u['localRoleToken']]+ids+[2]);turns+=1;body+=len(ids);roles+=1
            assert list(values[offset:offset+len(expected)])==expected,d['id']
            for start in range(0,len(expected)-1,256):
                length=min(257,len(expected)-start)
                if length>=2:allrows[(d['id'],start)]={'offset':offset+start,'length':length}
            offset+=len(expected)
        assert offset==len(values)
        for row in data[p+'Windows']:
            ref=allrows[(row['document'],row['startToken'])]
            assert row['offset']==ref['offset']and row['length']==ref['length']
        if p=='train':
            assert len(allrows)==len(data[p+'Windows'])and sum(r['length']-1 for r in data[p+'Windows'])==len(values)-len(docs[p])
        assert values.count(1)==len(docs[p]) and values.count(2)==turns and values.count(3)+values.count(4)==roles
        assert values.count(0)==values.count(5)==0
        streamstats[p]={'documents':len(docs[p]),'tokens':len(values),'bodyTokens':body,'roleTokens':roles,'trueTurnEos':turns,
            'allDocumentStreamsMatchOriginalUtterances':True,'selectedWindowsValidated':len(data[p+'Windows']),
            'inputOnlyBos':len(docs[p]),'unknownGlyphOccurrencePreservedByByteFallback':data['statistics'][p]['unknownUnicodeOccurrences']}
    bench=read(base/'benchmark-dev.json');cases=bench['cases'];gold=collections.Counter(u['text']for d in docs['train']for u in d['utterances'])
    normalized_gold=collections.Counter(nrm(u['text'])for d in docs['train']for u in d['utterances'])
    queries=collections.defaultdict(set)
    for c in cases:
        h=[u['text']for u in c['history']];n=len(h)
        queries[n].add(signature(h));queries[n+1].add(signature(h+[c['targetText']]))
    matches=collections.Counter()
    for d in docs['train']:
        us=[u['text']for u in d['utterances']]
        for n,q in queries.items():
            for start in range(len(us)-n+1):
                sig=signature(us[start:start+n])
                if sig in q:matches[sig]+=1
    overlap=[]
    for c in cases:
        h=[u['text']for u in c['history']]
        overlap.append({'id':c['id'],'exactGoldUtteranceTrainOccurrences':gold[c['targetText']],
            'normalizedGoldUtteranceTrainOccurrences':normalized_gold[nrm(c['targetText'])],
            'exactHistoryTrainOccurrences':matches[signature(h)],'exactHistoryPlusGoldTrainOccurrences':matches[signature(h+[c['targetText']])]})
    result={'status':'PASS','modelInstantiated':False,'optimizerUpdates':0,'sourceScope':'Fresh-series existing human TRAIN only, no reserved TEST',
        'dataSha256':sha(a.data),'tokenizerSha256':data['tokenizerSha256'],'trainOnlyGlyphInventoryExact':True,
        'speakerAndNormalizedWholeDocumentFamiliesDisjoint':True,'noSourceDocumentMixedInWindows':True,'allTrueUtteranceEndEosVerified':True,
        'streamStatistics':streamstats,'benchmarkCases':len(cases),'benchmarkExactFullExampleOverlapCases':sum(x['exactHistoryPlusGoldTrainOccurrences']>0 for x in overlap),
        'benchmarkExactGoldOverlapCases':sum(x['exactGoldUtteranceTrainOccurrences']>0 for x in overlap),'overlap':overlap,
        'limits':'Exact overlap is not semantic-family independence; common phrases may recur. Unknown glyphs use raw bytes, never vocabulary fit from DEV.'}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='overlap'},ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);main(p.parse_args())
