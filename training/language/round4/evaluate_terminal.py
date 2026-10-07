"""Diagnose actual terminal weights separately from the VAL-selected export."""
import gzip,hashlib,json,pathlib,subprocess,sys,time
import torch
from train import export_model
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    run=ROOT/'boundary-focus-2000'
    while not (run/'result.json').exists():time.sleep(10)
    result=read(run/'result.json');assert result['completedRun'] and result['completedSteps']==2000
    assert sha(run/'checkpoint.pt')==result['checkpointSha256']
    saved=torch.load(run/'checkpoint.pt',map_location='cpu',weights_only=False)
    assert saved['step']==2000 and sorted({int(s['step']) for s in saved['optimizer']['state'].values()})==[2000]
    out=ROOT/'terminal-2000';out.mkdir(exist_ok=True);torch.set_num_threads(1)
    training=dict(**result,diagnosticOnly=True,diagnosticWeightStep=2000,notCanonicalValSelected=True,additionalOptimizerUpdates=False)
    training['selection']='Actual terminal2000 weights for development diagnosis only; run bestStep is canonical VAL choice, not this diagnostic weight step'
    export_model(None,saved['model'],read(ROOT/'boundary-bpe-8192/tokenizer.json'),saved['config'],training,out/'model.js');del saved
    packed=out/'model.js.gz';packed.write_bytes(gzip.compress((out/'model.js').read_bytes(),mtime=0))
    (out/'snapshot.json').write_text(json.dumps(dict(diagnosticOnly=True,actualTerminalUpdates=2000,additionalUpdates=False,checkpointSha256=result['checkpointSha256'],plainModelSha256=sha(out/'model.js'),gzipModelSha256=sha(packed),canonicalValChoiceStep=result['bestStep']),indent=2)+'\n')
    for command,log in [([sys.executable,str(ROOT/'evaluate.py'),'--model',str(out/'model.js'),'--partition','validation','--out',str(out/'validation.json'),'--reference'],out/'validation-generation.log'),(['node',str(ROOT.parent/'evaluate_js.mjs'),str(out/'model.js'),str(out/'validation.json'),str(out/'validation-js.json')],out/'validation-parity.log')]:
        with log.open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
    (out/'model.js').unlink()
    print(json.dumps(dict(diagnosticOnly=True,terminalUpdates=2000,additionalUpdates=False,testUsed=False)),flush=True)
if __name__=='__main__':main()
