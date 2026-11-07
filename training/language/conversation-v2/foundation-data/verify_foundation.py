"""Read-only audit of the archived candidate corpus and disabled learning plans."""
import collections,gzip,hashlib,json,pathlib,re,tarfile
HERE=pathlib.Path(__file__).resolve().parent;REPO=HERE.parents[3]
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def run():
    manifest=read(HERE/'archive-manifest.json');verified=[]
    for group in ['rawArchives','canonicalCorpus','proposedMatchedSchedule']:
        for r in manifest[group]:
            p=REPO/r['path'];assert p.stat().st_size==r['bytes']and sha(p)==r['sha256'],r['path'];verified.append(r['path'])
    raw=HERE/'archives/jaquad-train-05600ff310a0.tar.gz'
    shards={pathlib.Path(r['rawPath']).name:r for r in read(HERE/'sources/jaquad-acquisition.json')['shards']}
    with tarfile.open(raw,'r:gz')as archive:
        members=[m for m in archive if m.isfile()];assert len(members)==30
        for m in members:
            name=pathlib.Path(m.name).name;assert name in shards and 'train' in name
            f=archive.extractfile(m);b=f.read();f.close()
            assert len(b)==shards[name]['bytes']and hashlib.sha256(b).hexdigest()==shards[name]['sha256']
    receipt=read(HERE/'corpus/receipt.json');component_splits={};family_splits={};counts=collections.Counter();empty=collections.Counter()
    with gzip.open(HERE/'corpus/documents.jsonl.gz','rt')as f:
        for line in f:
            d=json.loads(line);assert d['source']in {'jaquad','jawikibooks','jawikivoyage'}and d['admission']=='candidate-not-admitted'
            component_splits.setdefault(d['component'],set()).add(d['split']);family_splits.setdefault(d['family'],set()).add(d['split'])
            ps=[p for p in d['paragraphs']if p['keepForCandidateTraining']]
            counts[d['split']]+=sum(p['ownBpeTokens']for p in ps);empty[d['split']]+=not bool(ps)
    assert all(len(x)==1 for x in component_splits.values())and all(len(x)==1 for x in family_splits.values())
    assert counts['train']==20262193 and sum(counts.values())==23351258
    assert all(counts[k]==v['retainedOwnBpeBodyTokens']for k,v in receipt['splitStats'].items())
    split=read(HERE/'corpus/article-splits.json');assert split['reserveIsSealedTest']is False
    evaluation=read(HERE/'evaluation/PLAN.json');assert not evaluation['inferenceAuthorized']and evaluation['optimizerUpdatesPermitted']==0
    assert evaluation['cases']==evaluation['supportedCases']==68
    assert evaluation['finalCombinedSplitSha256']==sha(HERE/'corpus/article-splits.json')
    for p,h in evaluation['codeAndDataReceipts'].items():assert sha(REPO/p)==h,p
    quality=read(HERE/'quality-reading.json');sample=read(HERE/'quality-sample.json')
    assert quality['fullRowsRead']==len(sample['rows'])==80 and quality['unread']==0
    assert quality['sampleSha256']==sha(HERE/'quality-sample.json')and sample['corpusSha256']==sha(HERE/'corpus/documents.jsonl.gz')
    assert {r['sampleHash']for r in quality['rows']}=={r['sampleHash']for r in sample['rows']}
    plan=read(HERE/'research/PREFLIGHT_PLAN.json');pf=read(HERE/'research/preflight-result.json')
    assert pf['planSha256']==sha(HERE/'research/PREFLIGHT_PLAN.json')
    for p,h in plan['codeReceipts'].items():assert sha(REPO/p)==h,p
    assert pf['actualOptimizerUpdates']==pf['optimizerStepAttempts']==0 and pf['forwardBackwardBatches']==4
    assert pf['beforeTrajectoryDigest']==pf['afterTrajectoryDigest'] and pf['modelAdamTorchPrivateRngSamplerOrderHistoryUnchanged']
    nextplan=read(HERE/'research/NEXT_EXPERIMENT_PLAN.json');assert not nextplan['trainingAuthorized']and nextplan['optimizerUpdatesPerformed']==0
    schedule=read(HERE/'research/matched-schedule/receipt.json');audit=read(HERE/'research/matched-schedule-audit.json')
    assert audit['passed']and audit['actualStepsAudited']==2048 and audit['perArmGenuineTargetTokens']==1735859
    assert schedule['selectedNativeTrueEndsTotal']==777 and not schedule['trainingAuthorized']
    assert sha(HERE/'research/matched-schedule/schedule.jsonl.gz')==schedule['scheduleSha256']
    files=[]
    for p in sorted(HERE.rglob('*')):
        if not p.is_file()or '__pycache__'in p.parts or p in {HERE/'verification.json',HERE/'verification.log'}:continue
        files.append(dict(path=str(p.relative_to(REPO)),bytes=p.stat().st_size,sha256=sha(p)))
    result=dict(passed=True,sourceArchives=3,jaquadTrainRawShards=30,allNewSourceDataCandidateOnly=True,
        candidateBodyTokens=23351258,candidateTrainBodyTokens=20262193,trainingEmptyDocumentsExcludedByNextSchedule=empty['train'],
        exactKnownFamilyAndComponentSplitOverlap=0,semanticFamilyDisjointnessProven=False,
        sealedTestCreated=False,sealedTestRead=False,evaluationPreparedCases=68,qualityFullParagraphsRead=80,
        actualOptimizerUpdates=0,zeroUpdateForwardBackwardBatches=4,modelStateUnchanged=True,
        proposedStepsPerArm=2048,proposedTargetsPerArm=1735859,proposedNativeTrueEnds=777,
        modelTrainingAuthorized=False,learningDecision='NO_GO',artifacts=files)
    (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='artifacts'},indent=2))
if __name__=='__main__':run()
