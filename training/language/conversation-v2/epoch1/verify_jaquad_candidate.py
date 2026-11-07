"""Verify the unadmitted human-QA TRAIN sample, never fetch DEV/TEST or models."""
import argparse,hashlib,json,pathlib,urllib.request
HERE=pathlib.Path(__file__).resolve().parent
def main(fetch):
    folder=HERE/'jaquad-candidate';receipt=json.loads((folder/'retrieval.json').read_text())
    if '/data/train/jaquad_train_0000.json'not in receipt['url']:raise ValueError('Only pinned first TRAIN shard allowed')
    raw=pathlib.Path('/dev/shm/epoch1-jaquad-train0000.json')
    if fetch:
        with urllib.request.urlopen(receipt['url'],timeout=25)as response:data=response.read(16000001)
        if len(data)>16000000:raise ValueError('Bounded candidate-source audit only')
        if hashlib.sha256(data).hexdigest()!=receipt['rawSha256']:raise ValueError('Pinned raw source changed')
        raw.write_bytes(data)
    data=raw.read_bytes()
    assert len(data)==receipt['bytes'] and hashlib.sha256(data).hexdigest()==receipt['rawSha256']
    source=json.loads(data)
    paragraphs=[(d['title'],i,p)for d in source['data']for i,p in enumerate(d['paragraphs'])]
    chosen=sorted(paragraphs,key=lambda z:hashlib.sha256(('epoch1-jaquad-quality-v1|'+z[0]+'|'+str(z[1])).encode()).hexdigest())[:30]
    expected=[dict(articleTitle=t,paragraphOrdinal=i,context=p['context'],qas=p['qas'])for t,i,p in chosen]
    sample=json.loads((folder/'sample.json').read_text());assert sample['rows']==expected
    audit=json.loads((folder/'audit.json').read_text())
    assert hashlib.sha256((folder/'sample.json').read_bytes()).hexdigest()==audit['sampleSha256']
    assert not audit['admitted'] and not audit['trainingUpdated'] and not audit['sealedTestOpened']
    for r in expected:
        for q in r['qas']:
            for a in q['answers']:assert r['context'][a['answer_start']:a['answer_start']+len(a['text'])]==a['text']
    print(json.dumps(dict(passed=True,contexts=30,questions=sum(len(r['qas'])for r in expected),
        sampleVerbatim=True,sourceSha256=receipt['rawSha256'],admitted=False,
        optimizerUpdates=0,sealedTestRead=False)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');main(p.parse_args().fetch)
