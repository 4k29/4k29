"""Replay/verify only pinned candidate TRAIN/public-wiki payloads, never models/TEST.

Default is verification only. --fetch uses the recorded immutable URLs and exact
byte hashes. This reproduces the acquired source payloads; admission is separate.
"""
import argparse,gzip,hashlib,json,pathlib,tarfile,urllib.request
HERE=pathlib.Path(__file__).resolve().parent
AGENT='OwnTransformerSourceAudit/0.1 (public research audit)'
def read(p):return json.loads(p.read_text())
def digest(p,algorithm='sha256'):
    h=hashlib.new(algorithm)
    with pathlib.Path(p).open('rb')as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def fetch(row,path):
    if not row['url'].startswith(('https://huggingface.co/datasets/SkelterLabsInc/JaQuAD/resolve/05600ff310a0970823e70f82f428893b85c71ffe/data/train/',
                                  'https://dumps.wikimedia.org/jawikibooks/20261001/',
                                  'https://dumps.wikimedia.org/jawikivoyage/20261001/')):
        raise ValueError('Only registered immutable TRAIN/wiki URLs permitted')
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.stat().st_size==row['bytes'] and digest(path)==row['sha256']:return
        raise ValueError('Refuse to replace a different existing payload')
    temporary=path.with_name(path.name+'.download.tmp');maximum=min(row['bytes'],64000000)
    try:
        req=urllib.request.Request(row['url'],headers={'User-Agent':AGENT})
        with urllib.request.urlopen(req,timeout=50)as response,temporary.open('wb')as out:
            total=0
            while block:=response.read(1048576):
                total+=len(block)
                if total>maximum:raise ValueError('Source exceeds recorded bounded size')
                out.write(block)
        if temporary.stat().st_size!=row['bytes']or digest(temporary)!=row['sha256']:raise ValueError('Immutable source identity changed')
        temporary.replace(path)
    finally:temporary.unlink(missing_ok=True)
def main(fetch_requested,output_root):
    if not str(output_root).startswith('/dev/shm/'):raise ValueError('Large payloads must remain in declared tmpfs')
    ja=read(HERE/'jaquad-acquisition.json');wiki=read(HERE/'wikimedia-acquisition.json');reports=[]
    for row in ja['shards']:
        target=output_root/'jaquad'/pathlib.Path(row['rawPath']).name
        if fetch_requested:fetch(row,target)
        assert target.stat().st_size==row['bytes']and digest(target)==row['sha256']
        document=read(target)
        assert len(document['data'])==row['articles']
        reports.append(dict(source='jaquad-train',part=row['part'],bytes=row['bytes'],sha256=row['sha256']))
    for row in wiki:
        target=output_root/row['source']/pathlib.Path(row['path']).name
        if fetch_requested:fetch(row,target)
        assert target.stat().st_size==row['bytes']and digest(target)==row['sha256']
        assert digest(target,'sha1')==row['officialSha1']and row['bytes']==row['officialSize']
        reports.append(dict(source=row['id'],bytes=row['bytes'],sha256=row['sha256'],officialSha1Verified=True))
    archive=output_root/'jaquad-train-05600ff310a0.tar.gz'
    if not archive.exists():
        with archive.open('wb')as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0,compresslevel=6)as gz,tarfile.open(fileobj=gz,mode='w')as tar:
            for row in ja['shards']:
                p=output_root/'jaquad'/pathlib.Path(row['rawPath']).name;info=tarfile.TarInfo(p.name)
                info.size=p.stat().st_size;info.mode=0o644;info.mtime=0
                with p.open('rb')as f:tar.addfile(info,f)
    record=read(HERE/'jaquad-archive.json')
    assert archive.stat().st_size==record['bytes']and digest(archive)==record['sha256']
    with tarfile.open(archive,'r:gz')as tar:
        assert len(tar.getmembers())==30
        for member,row in zip(tar.getmembers(),ja['shards'],strict=True):
            assert member.name==pathlib.Path(row['rawPath']).name
            assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==row['sha256']
    result=dict(passed=True,sourcePayloads=len(reports),downloadPayloadBytes=sum(r['bytes']for r in reports),
        rawArchiveBytes=record['bytes']+sum(r['bytes']for r in wiki),
        jaquadTrainContexts=ja['contexts'],jaquadTrainQuestions=ja['questions'],
        rawSourceIdentityVerified=True,qualifiedHumanTrainTokensNotEstablished=True,
        admitted=False,modelUpdates=0,pretrainedTokenizerObtained=False,sealedTestRead=False,payloads=reports)
    print(json.dumps(result,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');p.add_argument('--output-root',type=pathlib.Path,default=pathlib.Path('/dev/shm/foundation-data-source'))
    a=p.parse_args();main(a.fetch,a.output_root)
