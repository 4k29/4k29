"""Commit the final own-raw candidate before opening fresh TEST outputs."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    target=ROOT/'checkpoint-choice.json'
    if target.exists():raise RuntimeError('Selection is already frozen; do not replace it after TEST')
    if list(ROOT.glob('*/test.json')):raise RuntimeError('Fresh TEST was already evaluated')
    candidates=[]
    for name in ['raw-modern-million','prefix-million']:
        run=ROOT/name;result=read(run/'result.json');metrics=read(run/'metrics.json')
        assert result['completedRun'] and result['completedSteps']==result['requestedSteps']==10000
        assert metrics['bestStep']==result['bestStep']
        assert metrics['history'][-1]['step']==10000
        assert result['checkpointSha256']==sha(run/'checkpoint.pt')
        assert result['externalWeights']==result['externalTokenizer']==result['externalInferenceAPI']==False
        candidates.append(dict(run=name,selectedStep=result['bestStep'],validationNllPerUtf8Byte=metrics['bestValidationNllPerByte'],resultSha256=sha(run/'result.json'),metricsSha256=sha(run/'metrics.json'),checkpointSha256=result['checkpointSha256'],modelSha256=sha(run/'model.js'),tokenizerSha256=result['tokenizerSha256'],paragraphSelectionsSha256=result['paragraphSelectionsSha256']))
    assert candidates[0]['tokenizerSha256']==candidates[1]['tokenizerSha256']
    assert candidates[0]['paragraphSelectionsSha256']==candidates[1]['paragraphSelectionsSha256']
    selected=min(candidates,key=lambda c:c['validationNllPerUtf8Byte'])
    target.write_text(json.dumps(dict(chosenRun=selected['run'],candidates=candidates,criterion='Lowest full canonical held-paragraph NLL per UTF8 byte; same vocabulary, architecture and held targets',testUsed=False,policySha256=sha(ROOT/'generation-policy.json'),representationDecision='TRAIN-only prefix BPE boundaries and original layout added after inspecting development VAL outputs. Probe documents, thresholds, greedy decoding, vocabulary and held byte streams unchanged. No TEST output inspected.'),indent=2)+'\n')
    print(json.dumps(selected))
if __name__=='__main__':main()
