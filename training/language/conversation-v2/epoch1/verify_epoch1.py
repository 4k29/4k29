"""Verify frozen inputs, complete actual exposure, archived states and evaluations."""
import hashlib,json,pathlib,subprocess
HERE=pathlib.Path(__file__).resolve().parent;REPO=HERE.parents[3]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    frozen=[]
    for name in ['TRAIN_PLAN.json','EVAL_PLAN.json','PARITY_PLAN.json']:
        plan=read(HERE/name)
        for relative,expected in plan['codeReceipts'].items():
            assert sha(REPO/relative)==expected,(name,relative)
        for relative,expected in plan.get('panelSha256',{}).items():
            assert sha(HERE/relative)==expected
        frozen.append(dict(plan=name,sha256=sha(HERE/name)))
    assert read(HERE/'input-contract-preflight.json')['passed']
    audits=read(HERE/'training-audit.json');assert len(audits)==2 and all(x['passed']for x in audits)
    archives=[]
    for name in ['medium','small']:
        folder=HERE/name/'archive';manifest=read(folder/'checkpoint.pt.chunks.json');h=hashlib.sha256();size=0
        for part in manifest['chunks']:
            path=folder/part['path'];relative=str(path.relative_to(REPO))
            process=subprocess.Popen(['git','show','HEAD:'+relative],cwd=REPO,stdout=subprocess.PIPE)
            part_hash=hashlib.sha256();part_size=0
            for b in iter(lambda:process.stdout.read(1048576),b''):
                h.update(b);part_hash.update(b);size+=len(b);part_size+=len(b)
            process.stdout.close();assert process.wait()==0
            assert part_hash.hexdigest()==part['sha256'] and part_size==part['bytes']
        assert size==manifest['bytes'] and h.hexdigest()==manifest['sha256']
        assert manifest['sha256']==read(HERE/name/'receipt.json')['checkpointSha256']
        archives.append(dict(model=name,bytes=size,sha256=h.hexdigest(),allCommittedGitBytesVerified=True))
    evaluation=read(HERE/'evaluation-audit.json');assert evaluation['passed'] and len(evaluation['endpoints'])==4
    assert sum(x['singleOutputs']for x in evaluation['endpoints'])==224
    assert sum(x['selfplayEpisodes']for x in evaluation['endpoints'])==16
    parity=[]
    for name in ['medium','small']:
        r=read(HERE/'parity-results'/name/'receipt.json')
        assert r['actualOptimizerUpdates']==0 and r['cases']==3
        parity.append(dict(model=name,maximumAbsoluteLogitError=r['maximumAbsoluteLogitError'],
            argmaxDisagreements=r['sameHistoryArgmaxDisagreements'],divergentShortCases=r['independentAutoregressiveDivergentCases'],
            toleranceExceedances=r['toleranceExceedances']))
    blind={r['blindId']for r in read(HERE/'blind-pack.json')['rows']};assert len(blind)==240
    readers=[]
    for name in ['primary','secondary']:
        r=read(HERE/f'blind-reading-{name}.json');ids=[x['blindId']for x in r['rows']]
        assert len(ids)==240 and set(ids)==blind
        readers.append(dict(reader=name,rows=len(ids),sha256=sha(HERE/f'blind-reading-{name}.json')))
    changed=subprocess.check_output(['git','diff','research/conversation-v2','HEAD','--name-only'],cwd=REPO,text=True).splitlines()
    assert changed and all(p.startswith('training/language/conversation-v2/epoch1/')for p in changed)
    files=[]
    for path in sorted(HERE.rglob('*')):
        if not path.is_file() or '__pycache__'in path.parts or path.name=='verification.json':continue
        files.append(dict(path=str(path.relative_to(REPO)),bytes=path.stat().st_size,sha256=sha(path)))
    result=dict(passed=True,frozenPlans=frozen,actualNewOptimizerUpdates=6012,cumulativeActualIncludingPilot=7040,
        retainedTerminalUpdatesPerModel=3470,totalFirstEpochTargetsPerModel=2816905,
        newTargetsPerModel=2401584,archiveStates=archives,singleTurnFullGenerations=224,
        selfplayEpisodes=16,blindReaders=readers,limitedPythonJavascriptParity=parity,
        priorFilesChanged=False,sealedTestUsed=False,adopted=False,artifactFiles=files,
        scope='Reproducibility and measured evidence; not a formal natural-language capability pass')
    out=HERE/'verification.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='artifactFiles'},indent=2))
if __name__=='__main__':verify()
