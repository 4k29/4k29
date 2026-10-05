"""Snapshot own raw validation-selected state without changing the active run."""
import argparse,hashlib,json,pathlib
import torch
from model import Decoder
ROOT=pathlib.Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',type=pathlib.Path,required=True);args=p.parse_args()
 cp=ROOT/args.run/'checkpoint.pt';raw=cp.read_bytes();import io;saved=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=False)
 settings=saved['settings'];assert (settings['randomInitialization'] or settings.get('ownInitialModel',{}).get('kind','').startswith('Own raw-source Transformer')) and not settings['externalWeights'];assert settings['objective'].startswith('Raw original document causal')
 tok=json.loads((ROOT/f"bpe-{settings['merges']}"/'tokenizer.json').read_text());model=Decoder(saved['config'])
 paragraph=bool(settings.get('paragraphSelectionsSha256'))
 if paragraph:
  from train_paragraphs import export_model
 else:
  from train import export_model
 unit='canonical complete-paragraph' if paragraph else 'full-document'
 training=dict(**settings,completedRun=False,completedSteps=saved['step'],requestedSteps=settings['steps'],bestStep=saved['beststep'],parameters=sum(p.numel() for p in model.parameters()),snapshotCheckpointSha256=hashlib.sha256(raw).hexdigest(),seenTargetTokens=saved['seen_tokens'],seenTargetUtf8Bytes=saved['seen_bytes'],history=saved['history'],selection=f'Lowest held {unit} validation NLL per byte; diagnostic snapshot, not a completed run')
 export_model(model,saved['beststate'],tok,saved['config'],training,args.out);print(json.dumps(dict(completedUpdates=saved['step'],selectedStep=saved['beststep'],checkpointSha256=training['snapshotCheckpointSha256'])))
if __name__=='__main__':main()
