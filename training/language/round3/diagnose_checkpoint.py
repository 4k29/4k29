"""Reproduce intermediate raw FP32 continuations from retained own state."""
import argparse,hashlib,json,pathlib,torch
from evaluate import Decoder,generate,repetition
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--state',type=pathlib.Path,required=True);parser.add_argument('--compare',type=pathlib.Path,required=True);args=parser.parse_args()
    torch.set_num_threads(1);saved=torch.load(args.state,map_location='cpu',weights_only=False)
    prior=json.loads(args.compare.read_text());assert saved['diagnosticOnly'] and saved['optimizerNotIncluded']
    assert saved['step']==prior['checkpointCompletedUpdates'] and saved['beststep']==prior['selectedStep']
    assert hashlib.sha256(args.state.read_bytes()).hexdigest()==prior['retainedWeightsSha256']
    assert saved['sourceCheckpointSha256']==prior['checkpointSha256']
    tok=ROOT/f"raw-bpe-{saved['settings']['merges']}/tokenizer.json"
    assert hashlib.sha256(tok.read_bytes()).hexdigest()==prior['tokenizerSha256']
    policy=ROOT/'generation-policy.json';assert hashlib.sha256(policy.read_bytes()).hexdigest()==prior['policySha256']
    model=Decoder(saved['config']);model.load_state_dict(saved['beststate']);model.eval();vocab=json.loads(tok.read_text())
    for source,old in zip(json.loads(policy.read_text())['probes']['validation'],prior['rows'],strict=True):
        new=generate(model,source['prefix'],vocab,128)
        assert source['id']==old['id'] and source['prefix']==old['prefix']
        assert all(new[k]==old[k] for k in ['text','tokens','eos','validUtf8','validTokens','inputTokens'])
        assert repetition(new['text'])==old['repetitionDiagnostics']
        print(json.dumps(dict(id=source['id'],completeRawGenerationMatch=True)),flush=True)
    print(json.dumps(dict(diagnosticOnly=True,allRowsMatched=True,additionalUpdates=False,testUsed=False)))
if __name__=='__main__':main()
