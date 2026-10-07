"""Finalize already-saved source records after metadata-path failure.
No source text changes, retrieval replay, partition fitting or training.
"""
import datetime,gzip,hashlib,json,pathlib,re
from collect_mdn import ROOT,base,normalize,read,write
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=ROOT/'mdn-documents.jsonl';docs=[json.loads(x) for x in p.read_text().splitlines()]
    assert docs and len({d['id'] for d in docs})==len(docs)
    old=ROOT.parent/'round3/documents.jsonl';previous=[json.loads(x) for x in old.read_text().splitlines()]
    known={normalize(d[k]) for d in previous for k in ['url','finalUrl'] if d.get(k)}
    archivePaths=set()
    for d in docs:
        archive=ROOT/d['htmlArchive'];assert sha(archive)==d['htmlArchiveSha256']
        raw=gzip.decompress(archive.read_bytes());assert hashlib.sha256(raw).hexdigest()==d['htmlSha256']
        source,encoding=base.decode(raw);assert encoding==d['encoding']
        parser=base.Prose();parser.feed(source)
        blocks=[dict(sourceBlockIndex=i,**b) for i,b in enumerate(parser.blocks) if b['tag']=='p' and len(b['text'])>=40 and b['text'][-1:] in '。！？」' and not base.boilerplate(b['text'])]
        assert blocks==d['blocks'];assert '\n'.join(b['text'] for b in blocks)==d['text']
        assert hashlib.sha256(d['text'].encode()).hexdigest()==d['textSha256']
        assert normalize(d['finalUrl']) not in known
        assert d['license']=='CC BY-SA 4.0' and d['author']=='MDN contributors'
        archivePaths.add(archive.resolve())
    assert archivePaths=={x.resolve() for x in (ROOT/'source-html').glob('*.gz')}
    policy=ROOT/'source-discovery/copyright-policy.html';robots=ROOT/'source-discovery/robots.txt';tree=read(ROOT/'source-discovery/ja-web-tree.json')
    report=dict(retrievedAt=docs[0]['retrievedAt'],verifiedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),documents=len(docs),characters=sum(len(d['text']) for d in docs),utf8Bytes=sum(len(d['text'].encode()) for d in docs),documentsSha256=sha(p),creditsSha256=sha(ROOT/'mdn-credits.json'),executedCollectorSourceSha256=sha(ROOT/'collector-executed-before-metadata-fix.py.txt'),correctedCollectorSourceSha256=sha(ROOT/'collect_mdn.py'),verifierSourceSha256=sha(pathlib.Path(__file__)),parserSourceSha256=sha(ROOT.parents[1]/'dialogue/collect_mdn_language.py'),baseCollectorSourceSha256=sha(ROOT.parent/'collect_sources.py'),previousDocumentsSha256=sha(old),copyrightPolicySha256=sha(policy),robotsSha256=sha(robots),discoveryCommit=read(ROOT/'source-discovery/commit-metadata.json')['sha'],discoveryTreeSha=tree['sha'],requestedUrls=1500,retrievalLoopCompleted=True,metadataFinalizationError='Incorrect parser source path after records/credits were saved; corrected and separately replay-verified every saved HTML against untouched paragraphs.',finalizedWithSeparateVerifier=True,failed=None,skipped=None,attemptFailureAndSkipDetailsNotRetained=True,sourceArchiveFilesVerified=len(archivePaths),partitionsNotAssigned=True,notUsedByRunningRound6=True,tokenizerNotFitted=True,optimizerUpdates=0,externalWeights=False,externalTokenizer=False,externalInferenceAPI=False,wikipedia=False)
    write(ROOT/'mdn-sources.json',report)
    print(json.dumps({k:report[k] for k in ['documents','characters','utf8Bytes','sourceArchiveFilesVerified','partitionsNotAssigned','optimizerUpdates']}),flush=True)
if __name__=='__main__':main()
