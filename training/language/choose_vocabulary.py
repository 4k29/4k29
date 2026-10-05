"""Select own vocabulary by validation byte NLL only, never test outcomes."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent

def main():
    rows=[]
    for merges in [2048,4096]:
        folder=ROOT/f'pilot-{merges}';result=json.loads((folder/'result.json').read_text());metrics=json.loads((folder/'metrics.json').read_text())
        assert result['completedRun'] and result['completedSteps']==1000 and result['randomInitialization'] and not result['externalWeights']
        best=next(r for r in metrics['history'] if r['step']==result['bestStep']);data=json.loads((ROOT/f'bpe-{merges}'/'data.json').read_text())
        rows.append(dict(merges=merges,vocabulary=data['vocabulary'],parameters=result['parameters'],bestStep=result['bestStep'],completedUpdates=result['completedSteps'],validation=best['validation'],trainUtf8Bytes=data['stats']['train']['utf8Bytes'],validationUtf8Bytes=data['stats']['validation']['utf8Bytes'],seenTargetUtf8Bytes=result['seenTargetUtf8Bytes'],modelSha256=hashlib.sha256((folder/'model.js').read_bytes()).hexdigest(),tokenizerSha256=data['tokenizerSha256'],sourceSha256=data['sourceSha256'],splitSha256=data['splitSha256']))
    assert rows[0]['sourceSha256']==rows[1]['sourceSha256'];assert rows[0]['validationUtf8Bytes']==rows[1]['validationUtf8Bytes']
    winner=min(rows,key=lambda row:row['validation']['nllPerUtf8Byte']);decision=dict(selection='Minimum held full-document validation NLL per UTF8 byte; no TEST likelihood or generation viewed',rows=rows,selectedMerges=winner['merges'],selectedVocabulary=winner['vocabulary'],note='Token perplexity cannot be compared across vocabularies. Different embedding parameter counts, context measured in tokens and training byte exposure also change with vocabulary; this is an operational pilot choice, not an isolated causal proof that vocabulary size improves language. Pilot generation is developmental validation only, not acceptance evidence.')
    (ROOT/'vocabulary-choice.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(selectedMerges=winner['merges'],scores={r['merges']:r['validation']['nllPerUtf8Byte'] for r in rows})))
if __name__=='__main__':main()
