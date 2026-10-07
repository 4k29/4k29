"""Freeze actual selected weights at a saved update; never invent completion."""
import argparse,gzip,json,pathlib,sys
sys.path.insert(1,str(pathlib.Path(__file__).resolve().parent.parent))
import torch
from train import export_model,sha,write,ROOT
def main():
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=pathlib.Path,required=True);p.add_argument('--expected-step',type=int,required=True);p.add_argument('--out',type=pathlib.Path,required=True);args=p.parse_args();saved=torch.load(args.checkpoint,map_location='cpu',weights_only=False)
    if saved['step']!=args.expected_step:raise ValueError('Actual saved update differs from requested snapshot')
    counters=sorted({int(s['step']) for s in saved['optimizer']['state'].values()})
    if counters!=[saved['step']]:raise ValueError('Optimizer counters disagree with saved step')
    training=dict(**saved['settings'],completedRun=False,diagnosticSnapshot=True,completedSteps=saved['step'],requestedSteps=saved['settings']['steps'],bestStep=saved['beststep'],parameters=sum(t.numel() for t in saved['beststate'].values()),seenTargetTokens=saved['seen_tokens'],seenTargetUtf8Bytes=saved['seen_bytes'],checkpointSha256=sha(args.checkpoint),selection='Lowest canonical VAL byte NLL at saved update; diagnostic VAL only, TEST not evaluated',history=saved['history'])
    args.out.mkdir(parents=True,exist_ok=True);plain=args.out/'model.js';export_model(None,saved['beststate'],None,saved['config'],training,plain)
    # Tokenizer is fixed by hash; inject our own vocabulary, never an outside one.
    tokenizer_path=ROOT/f"paragraph-bpe-{saved['settings']['merges']}"/'tokenizer.json'
    if sha(tokenizer_path)!=saved['settings']['tokenizerSha256']:raise ValueError('Vocabulary identity changed')
    source=plain.read_text();export=json.loads(source.split('export const dialogueModel=',1)[1].strip().removesuffix(';'));export['tokenizer']=json.loads(tokenizer_path.read_text());plain.write_text('export const dialogueModel='+json.dumps(export,ensure_ascii=False,separators=(',',':'))+';\n')
    packed=args.out/'model.js.gz';packed.write_bytes(gzip.compress(plain.read_bytes(),mtime=0))
    write(args.out/'snapshot.json',dict(actualSavedUpdates=saved['step'],selectedStep=saved['beststep'],requestedRunUpdates=saved['settings']['steps'],completedRequestedRun=False,optimizerStepCounters=counters,torchRngSaved=True,pythonRngSaved=True,sourceCheckpointSha256=sha(args.checkpoint),uncompressedModelSha256=sha(plain),compressedModelSha256=sha(packed),config=saved['config'],training=training))
    print(json.dumps(dict(actualSavedUpdates=saved['step'],selectedStep=saved['beststep'],completedRequestedRun=False)),flush=True)
if __name__=='__main__':main()
