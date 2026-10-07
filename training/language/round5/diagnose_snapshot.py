"""Early raw development diagnosis from the immutable own1000 checkpoint."""
import hashlib,json,pathlib,sys,time,torch
from evaluate import Decoder,generate,repetition
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    torch.set_num_threads(1);path=ROOT/'characters-10000/checkpoint-1000.pt'
    saved=torch.load(path,map_location='cpu',weights_only=False)
    assert saved['step']==1000 and sorted({int(s['step']) for s in saved['optimizer']['state'].values()})==[1000]
    assert saved['settings']['randomInitialization'] and saved['settings']['unicodeCharacterAssembly']
    model=Decoder(saved['config']);model.load_state_dict(saved['beststate']);model.eval()
    tok=json.loads((ROOT/'unicode-bpe-4503/tokenizer.json').read_text());policy=json.loads((ROOT/'generation-policy.json').read_text());rows=[];begun=time.monotonic()
    for source in policy['probes']['validation']:
        result=generate(model,source['prefix'],tok,policy['generation']['maxNewTokens'])
        rows.append(dict(id=source['id'],site=source['site'],prefix=source['prefix'],**result,repetitionDiagnostics=repetition(result['text'])))
        print(json.dumps(dict(id=source['id'],joined=source['prefix']+result['text'],eos=result['eos'],validTokens=result['validTokens']),ensure_ascii=False),flush=True)
    report=dict(diagnosticOnly=True,partition='validation',checkpointCompletedUpdates=1000,selectedStep=saved['beststep'],checkpointSha256=hashlib.sha256(path.read_bytes()).hexdigest(),directFullPrecisionInference=True,notFinalWeightSelection=True,testUsed=False,maxNewTokens=192,rows=rows,elapsedSeconds=time.monotonic()-begun,diagnosticSourceSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest())
    (ROOT/'diagnostic-1000.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
