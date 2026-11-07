"""Verify immutable TRAIN originals/tokens and derive authentic turn spans only."""
import argparse, collections, hashlib, json, pathlib, sys, time
import numpy as np


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def build(root, output):
    begun=time.monotonic()
    index_path=root/'multiview/train.index.json'
    index=json.loads(index_path.read_text())
    token_path=root/'multiview/train.tokens.bin'
    assert sha(token_path)==index['tokensSha256']
    tokens=np.memmap(token_path,dtype='<u4',mode='r')
    tokenizer_path=root/'multiview/tokenizer.json'
    vocabulary=[bytes.fromhex(s) for s in json.loads(tokenizer_path.read_text())['bytes']]
    lengths=np.array([len(s) for s in vocabulary],dtype=np.int64)
    rp_path=root/'sources/documents.jsonl'
    jmrd_path=root/'added-human-source/documents.jsonl'
    documents={}
    for path in [rp_path,jmrd_path]:
        for line in path.open():
            d=json.loads(line)
            assert d['partition']=='train' and d['site']=='human-chat'
            if d['originalDocument'] in documents:
                assert documents[d['originalDocument']]==d
                continue
            documents[d['originalDocument']]=d
    raw_jmrd=pathlib.Path('/workspace/next-source-candidate-jmrd/upstream-train.json')
    jmrd_hash=sha(raw_jmrd)
    manifest=json.loads((root/'added-human-source/manifest.json').read_text())
    assert jmrd_hash==manifest['rawTrainSha256']
    jmrd={d['dialog_id']:d for d in json.loads(raw_jmrd.read_text())}
    raw_rp=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train')
    units=collections.defaultdict(list)
    for unit in index['documents']:
        if unit['site']=='human-chat':units[unit['sourceDocument']].append(unit)
    assert set(units)==set(documents)
    output_units={};counts=collections.Counter();per_view=collections.defaultdict(collections.Counter)
    raw_rp_receipts=[]
    for k,(source_id,d) in enumerate(documents.items()):
        source='jmrd' if source_id.startswith('jmrd:') else 'realpersona'
        if source=='jmrd':
            assert d['sourceSha256']==jmrd_hash and d['upstreamPartition']=='train'
            original=jmrd[d['dialogueIdMetadata']]
            texts=[u['text'] for u in original['dialog']]
        else:
            raw_path=raw_rp/pathlib.PurePosixPath(d['sourcePath']).name
            raw=raw_path.read_bytes();raw_hash=hashlib.sha256(raw).hexdigest()
            assert raw_hash==d['sourceSha256']
            raw_rp_receipts.append((source_id,raw_hash))
            texts=[u['text'] for u in json.loads(raw)['utterances']]
        assert len(texts)==d['utteranceCount']
        text='\n'.join(texts);payload=text.encode('utf-8')
        assert text==d['text'] and hashlib.sha256(payload).hexdigest()==d['textSha256']
        endpoints=[0];offset=0
        for j,t in enumerate(texts):
            offset+=len(t.encode('utf-8'))+(j<len(texts)-1)
            endpoints.append(offset)
        assert offset==len(payload)
        counts[source+'Documents']+=1;counts[source+'Utterances']+=len(texts)
        counts['embeddedOriginalNewlines']+=sum(t.count('\n') for t in texts)
        counts['emptyOriginalUtterances']+=sum(not t for t in texts)
        assert {u['variant'] for u in units[source_id]}=={0,1,2} and len(units[source_id])==3
        for unit in units[source_id]:
            seq=tokens[unit['offset']:unit['offset']+unit['length']]
            assert int(seq[0])==1 and int(seq[-1])==2
            assert b''.join(vocabulary[int(t)] for t in seq)==payload
            sums=np.concatenate((np.array([0],dtype=np.int64),np.cumsum(lengths[seq])))
            assert int(sums[-1])==len(payload)
            aligned=[]
            for n,b in enumerate(endpoints):
                if n==0:j=1
                elif n==len(endpoints)-1:j=len(seq)-1
                else:j=int(np.searchsorted(sums,b,side='left'))
                if j<len(sums) and int(sums[j])==b:
                    aligned.append(j)
                else:aligned.append(None)
            assert aligned[0]==1 and aligned[-1]==len(seq)-1
            spans=[[j,aligned[j],aligned[j+1]] for j in range(len(texts))]
            output_units[unit['id']]=spans
            v=per_view[(source,unit['variant'])]
            v['units']+=1;v['authenticTurns']+=len(spans)
            v['alignedEndpoints']+=sum(x is not None for x in aligned)
            v['unalignedEndpoints']+=sum(x is None for x in aligned)
            v['completeAlignedTurns']+=sum(a is not None and b is not None for _,a,b in spans)
            v['completeAlignedNonemptyTurns']+=sum(a is not None and b is not None and a<b for _,a,b in spans)
        if (k+1)%2000==0:print(json.dumps(dict(verifiedDocuments=k+1,elapsedSeconds=round(time.monotonic()-begun,2))),flush=True)
    feature=dict(schemaVersion=1,partition='TRAIN ONLY',coordinateConvention='Original token indices including BOS0; [start,end) includes original separator where present, excludes BOS/EOS; all authentic turn ordinals retained, unaligned endpoints null',
        sourceDocumentsSha256=sha(rp_path),addedSourceDocumentsSha256=sha(jmrd_path),
        trainIndexSha256=sha(index_path),trainTokensSha256=index['tokensSha256'],tokenizerSha256=sha(tokenizer_path),
        rawJmrdTrainSha256=jmrd_hash,rawRealpersonaVerifiedReceiptsSha256=hashlib.sha256(json.dumps(raw_rp_receipts,separators=(',',':')).encode()).hexdigest(),
        builderSha256=sha(pathlib.Path(__file__)),turnsByUnit=output_units)
    output.write_text(json.dumps(feature,ensure_ascii=False,separators=(',',':'))+'\n')
    audit=dict(scope='All admitted authentic human TRAIN sources and all three original own-token views; DEV/TEST files never opened',
        verifiedDocuments=len(documents),verifiedUnits=len(output_units),counts=dict(counts),
        perSourceView={f'{s}:view{v}':dict(c) for (s,v),c in sorted(per_view.items())},
        featureSha256=sha(output),featureBytes=output.stat().st_size,
        builderSha256=sha(pathlib.Path(__file__)),elapsedSeconds=time.monotonic()-begun,
        sourceTextUnchanged=True,retokenization=False,allOriginalTokenStreamsVerified=True,additionalOptimizerUpdates=0)
    output.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,default=pathlib.Path('/workspace/4k29/training/language/round47'));p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('/workspace/round48-response-turns.json'));a=p.parse_args();build(a.root,a.out)
