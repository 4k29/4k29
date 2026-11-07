"""Read-only audit of the completed bounded pilot and archived artifacts."""
import argparse,hashlib,json,pathlib,subprocess
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2]
def read(p):return json.loads(p.read_text())
def sha(p):
    d=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):d.update(b)
    return d.hexdigest()
def archive(path,expected):
    manifest=path.with_name(path.name+'.chunks.json')
    if manifest.exists():
        m=read(manifest);d=hashlib.sha256();n=0
        for part in m['chunks']:
            p=manifest.parent/part['path'];assert sha(p)==part['sha256'] and p.stat().st_size==part['bytes']
            with p.open('rb')as f:
                for b in iter(lambda:f.read(1048576),b''):d.update(b);n+=len(b)
        assert n==m['bytes'] and d.hexdigest()==m['sha256']==expected
    else:assert sha(path)==expected
def main(a):
    plan=read(H/'PLAN.json');ph=sha(H/'PLAN.json');data=read(ROOT/plan['dataPath'])
    assert sha(ROOT/plan['dataPath'])==plan['dataSha256']
    for p,h in plan['codeReceipts'].items():assert sha(ROOT/p)==h,p
    for key in ['tokenizer','trainTokens','devTokens']:
        assert sha(ROOT/data[key+'Path'])==data[key+'Sha256']
    assert sha(ROOT/data['benchmarkPath'])==data['benchmarkSha256']
    assert sha(ROOT/plan['evaluation']['annotationPath'])==plan['evaluation']['annotationSha256']
    split=read(H/'data/split.json');assert not set(split['trainSpeakers'])&set(split['devSpeakers'])
    source_count=0
    if a.sources:
        for row in split['rows']:
            p=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train')/(row['id'].split(':')[1]+'.json')
            assert sha(p)==row['sourceSha256'];source_count+=1
        for item in data['sourceReceipts']:assert sha(ROOT/item['path'])==item['sha256']
    receipts={};actual=0
    for name in ['small','medium']:
        p=H/'pilot'/name;r=read(p/'receipt.json');receipts[name]=r
        assert r['uniqueUpdates']==512 and r['actualOptimizerUpdates']==514 and r['replayOptimizerUpdates']==2
        assert r['finalAdamCounters']==[512.] and r['resumeAudit']['allModelOptimizerRngSamplerAndTraceBitwiseEqual']
        assert r['planSha256']==ph and r['dataSha256']==plan['dataSha256']
        events=[json.loads(s)for s in (p/'optimizer-ledger.jsonl').read_text().splitlines()]
        before=[x for x in events if x['event']=='before-step'];after=[x for x in events if x['event']=='after-step']
        assert len(before)==len(after)==514 and [x['actualUpdate']for x in after]==list(range(1,515))
        assert sum(x['replay']for x in after)==2;actual+=len(after)
        archive(p/'checkpoint.pt',r['checkpointSha256'])
    assert actual==1028
    for x,y in zip(receipts['small']['history'],receipts['medium']['history'],strict=True):
        for key in ['windowIndices','targetTokens','eosPositions','rolePositions','learningRate','samplerRngDigest']:assert x[key]==y[key]
    count=0
    for name,n in [('small',32),('medium',32),('r46',23)]:
        e=H/'evaluation'/name;r=read(e/'receipt.json');gs=read(e/'generations.json')
        assert r['status']=='complete' and r['optimizerUpdates']==0 and r['modelAndTorchRngUnchanged']
        assert r['supportedGenerations']==n and len(gs)==32
        tok=read(ROOT/'training/language/round46/multiview/tokenizer.json')if name=='r46'else read(ROOT/data['tokenizerPath'])
        pieces=[bytes.fromhex(x)for x in tok['bytes']]
        for g in gs:
            if not g['generationSupported']:assert name=='r46';continue
            count+=1;raw=b''.join(pieces[t]for t in g['nonEosTokens']);assert raw.hex()==g['rawBytesHex']
            assert g['tokensIncludingEos']==g['nonEosTokens']+([2]if g['eos']else[])
            if g['strictUtf8']:assert raw.decode('utf8')==g['text']
        if name!='r46':
            rows=read(e/'window-tf.json');assert len(rows)==64
            episodes=read(e/'selfplay.json');assert len(episodes)==4
            for episode in episodes:
                assert episode['requestedTurns']==3 and len(episode['rows'])<=3
                for step in episode['rows']:
                    g=step['generation'];assert b''.join(pieces[t]for t in g['nonEosTokens']).hex()==g['rawBytesHex']
    assert count==87
    for name,path,n in [('eval','blind-input.json',87),('model','blind-new-input.json',64)]:
        x=read(H/'evaluation'/('blind-reading-'+name+'.json'));inputs=H/'evaluation'/path
        assert x['blindInputSha256']==sha(inputs) and len(x['rows'])==n
        assert {r['blindId']for r in x['rows']}=={r['blindId']for r in read(inputs)} and all(r['readComplete']for r in x['rows'])
    sr=read(H/'evaluation/blind-selfplay-reading.json')
    assert len(sr['rows'])==8 and all(r['readComplete']for r in sr['rows'])
    assert sr['blindInputSha256']==sha(H/'evaluation/blind-selfplay-input.json')
    for name in ['small','medium']:
        r=read(H/'parity-results'/name/'receipt.json')
        assert r['cases']==3 and r['actualOptimizerUpdates']==0 and r['temporaryBinaryDeletedAfterVerification']
        assert r['originalCheckpointModelAndTorchRngUnchanged']
        assert r['toleranceExceedances']==0 and r['sameHistoryArgmaxDisagreements']==0
        assert r['independentAutoregressiveDivergentCases']==0
    tp=read(H/'TOKENIZER_PARITY_PLAN.json');tr=read(H/'tokenizer-parity/receipt.json')
    assert tr['planSha256']==sha(H/'TOKENIZER_PARITY_PLAN.json')
    assert tr['cases']==531 and tr['tokenIdMismatches']==0 and tr['utf8RoundtripFailures']==0
    assert tr['unknownGlyphTypesCovered']==19 and tr['optimizerUpdates']==0 and not tr['modelWeightsRead']
    assert sha(H/'tokenizer-parity/node-results.json')==tr['nodeResultsSha256']
    checked=0
    if a.manifest:
        for p,h in read(H/'artifact-manifest.json')['files'].items():
            path=H/p;assert sha(path)==h,p;checked+=1
            if a.tracked:subprocess.run(['git','ls-files','--error-unmatch',str(path.relative_to(ROOT))],cwd=ROOT,stdout=subprocess.DEVNULL,check=True)
    print(json.dumps({'status':'PASS','actualOptimizerUpdates':actual,'retainedUpdatesEach':512,'replayUpdatesTotal':4,
        'sourceOriginalsChecked':source_count,'fullSingleTurnGenerations':count,'blindReadSingleTurnsPrimary':87,
        'independentNewSingleTurnReadings':64,'selfplayEpisodesRead':8,'newTfWindows':128,
        'limitedRawFP32PythonJsPrefixes':6,'artifactFilesChecked':checked,'trackedChecked':a.tracked,
        'pythonJavascriptTokenizerInputsMatched':531,
        'languageCapabilityEstablished':False,'sealedTestUsed':False,'modelOrSiteReplacement':False,
        'cautions':'Not full192 JS parity; semantic-end rubric differs across graders; new-new only controlled width comparison'},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sources',action='store_true');p.add_argument('--manifest',action='store_true');p.add_argument('--tracked',action='store_true');main(p.parse_args())
