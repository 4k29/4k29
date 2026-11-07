"""Read-only artifact/data/state accounting checks; never restores or updates."""
import argparse, hashlib, json, pathlib, subprocess, sys
import torch
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[3]
def sha(p):
    d=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):d.update(b)
    return d.hexdigest()
def read(p):return json.loads(p.read_text())
def main(a):
    panel=read(H/'candidate-panel.json');plan=read(H/'PLAN.json')
    assert sha(H/'candidate-panel.json')==plan['panelSha256']
    for path,expected in plan['codeReceipts'].items():assert sha(ROOT/path)==expected,path
    assert sha(ROOT/plan['initialCheckpoint'])==plan['initialCheckpointSha256']
    if a.sources:
        for x in panel['inputReceipts']:
            path=pathlib.Path(x['path']);path=path if path.is_absolute()else ROOT/path
            assert sha(path)==x['sha256'],str(path)
    cs=panel['cases'];assert len(cs)==96 and len({c['document']for c in cs})==96
    for g,n in [('fit',64),('heldaside',32)]:
        rows=[c for c in cs if c['group']==g];assert len(rows)==n
        assert sorted(tuple(c['conditions']['correct']['prefixTokens'])for c in rows)==sorted(tuple(c['conditions']['mismatched']['prefixTokens'])for c in rows)
        assert all(len(c['conditions']['correct']['prefixTokens'])==len(c['conditions']['mismatched']['prefixTokens'])for c in rows)
    assert not set(panel['fitUniqueSpeakers'])&set(panel['heldasideUniqueSpeakers'])
    receipts={};actual=0
    for arm in ['A','B']:
        d=H/'training'/arm;r=read(d/'receipt.json');receipts[arm]=r
        assert r['actualOptimizerUpdates']==200 and r['uniqueUpdates']==198 and r['replayOptimizerUpdates']==2
        assert r['finalAdamCounters']==[29698.] and r['resume']['allStateAndTraceBitwiseEqual']
        ledger=[json.loads(s)for s in (d/'optimizer-ledger.jsonl').read_text().splitlines()]
        after=[x for x in ledger if x['event']=='after-step'];before=[x for x in ledger if x['event']=='before-step']
        assert len(after)==len(before)==200 and [x['actualUpdate']for x in after]==list(range(1,201))
        assert sum(x['replay']for x in after)==2;actual+=len(after)
        manifest=d/'terminal.pt.chunks.json'
        if manifest.exists():
            m=read(manifest);combined=hashlib.sha256();size=0
            for x in m['chunks']:
                path=d/x['path'];assert sha(path)==x['sha256'] and path.stat().st_size==x['bytes']
                with path.open('rb')as f:
                    for b in iter(lambda:f.read(1048576),b''):combined.update(b);size+=len(b)
            assert combined.hexdigest()==m['sha256']==r['terminalSha256'] and size==m['bytes']
        else:assert sha(d/'terminal.pt')==r['terminalSha256']
        if (d/'terminal.pt').exists():
            s=torch.load(d/'terminal.pt',map_location='cpu',weights_only=False)
            assert s['actualOptimizerUpdates']==200 and s['uniqueUpdates']==198
            assert sorted({float(x['step'])for x in s['optimizer']['state'].values()})==[29698.]
    assert actual==400
    for k in ['initialModelDigest','initialOptimizerDigest']:assert receipts['A'][k]==receipts['B'][k]
    for a1,b1 in zip(receipts['A']['history'],receipts['B']['history'],strict=True):
        for k in ['ids','targetTokens','torchRngDigest','pythonRngDigest']:assert a1[k]==b1[k]
    tokenizer=read(ROOT/panel['tokenizerPath']);pieces=[bytes.fromhex(x)for x in tokenizer['bytes']]
    total_tf=0;total_gen=0
    for e in ['baseline','A','B']:
        d=H/'results'/e;tf=read(d/'tf.json');gs=read(d/'generations.json');r=read(d/'receipt.json')
        assert len(tf)==192 and len(gs)==64 and r['inferenceOptimizerUpdates']==0 and r['modelAndTorchRngUnchanged']
        total_tf+=len(tf);total_gen+=len(gs)
        for x in gs:
            assert b''.join(pieces[t]for t in x['nonEosTokens']).hex()==x['rawBytesHex']
            if x['strictUtf8']:assert bytes.fromhex(x['rawBytesHex']).decode()==x['text']
            assert x['tokensIncludingEos']==x['nonEosTokens']+([2]if x['eos']else[])
    assert total_tf==576 and total_gen==192
    if a.reading:
        blind=read(H/'results/blind-input.json');expected={r['blindId']for r in blind}
        reports=[read(H/'results'/n)for n in ['fit-blind-reading.json','heldaside-blind-reading.json']]
        assert all(r['blindInputSha256']==sha(H/'results/blind-input.json')for r in reports)
        readings=[r for report in reports for r in report['rows']]
        assert len(readings)==192 and {r['blindId']for r in readings}==expected
        assert all(r['readComplete'] is True for r in readings)
    artifactcount=0
    if a.manifest:
        m=read(H/'artifact-manifest.json')
        for n,h in m['files'].items():
            path=H/n;assert sha(path)==h,n
            if a.require_tracked:
                subprocess.run(['git','ls-files','--error-unmatch',str(path.relative_to(ROOT))],cwd=ROOT,stdout=subprocess.DEVNULL,check=True)
        artifactcount=len(m['files'])
    print(json.dumps({'status':'PASS','actualOptimizerUpdates':actual,'retainedUniqueUpdates':396,'replayUpdates':4,
        'teacherForcedRows':total_tf,'fullRawGenerations':total_gen,'originalInputsChecked':len(panel['inputReceipts'])if a.sources else 0,
        'allBlindRead':a.reading,'artifactFilesChecked':artifactcount,'trackedArtifactsChecked':a.require_tracked,
        'initialCheckpointUnchanged':True,'sealedTestRead':False,
        'limits':'Not exact finite cumulative context marginals; no unseen TEST, no new JS parity or formal adoption claim'},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sources',action='store_true');p.add_argument('--reading',action='store_true')
    p.add_argument('--manifest',action='store_true');p.add_argument('--require-tracked',action='store_true');main(p.parse_args())
