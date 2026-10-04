"""Frozen raw-language evaluation on entire source pages excluded from fitting.

Measure next-token loss, not chat quality. The random-weight control uses this
same own architecture and vocabulary; no external model participates.
"""
import argparse
import json
import math
import pathlib
import torch
from torch.nn import functional as F
from train import DialogueDecoder,pack
from tokenizer import SPECIALS

parser=argparse.ArgumentParser()
parser.add_argument('--model',required=True)
parser.add_argument('--corpus',required=True)
parser.add_argument('--out',required=True)
args=parser.parse_args()
torch.set_num_threads(1)
source=pathlib.Path(args.model).read_text()
exported=json.loads(source.split('export const dialogueModel=',1)[1].strip().removesuffix(';'))
corpus=json.loads(pathlib.Path(args.corpus).read_text())
if exported['training']['sourceSha256']!=corpus['sourceSha256']:raise ValueError('Frozen model/source mismatch')
if exported['tokenizer']!=corpus['tokenizer']:raise ValueError('Vocabulary mismatch')
seen={r['text'] for key in ['pretraining','pretrainingValidation'] for r in corpus[key]}
excluded=[r for r in corpus['pretrainingTest'] if r['text'] in seen]
held=[r for r in corpus['pretrainingTest'] if r['text'] not in seen]
rows=[dict(tokens=r['tokens'],prefixLength=1) for r in held]
if not rows:raise ValueError('No independent raw-language test chunks remain')
x,y=pack(rows,SPECIALS['pad'],max(len(r['tokens'])-1 for r in rows))
@torch.no_grad()
def measure(model):
    model.eval();loss,count=0.0,0
    for start in range(0,len(x),32):
        targets=y[start:start+32]
        loss+=F.cross_entropy(model(x[start:start+32]).reshape(-1,exported['config']['vocabulary']),targets.reshape(-1),reduction='sum').item()
        count+=targets.ne(-100).sum().item()
    return dict(tokens=count,loss=loss/count,perplexity=math.exp(loss/count))
torch.manual_seed(exported['training']['seed'])
model=DialogueDecoder(exported['config']);random_control=measure(model)
model.load_state_dict({key:torch.tensor(t['data']).reshape(t['shape']) for key,t in exported['tensors'].items()})
frozen=measure(model)
report=dict(version=exported['version'],sourceSha256=corpus['sourceSha256'],samples=len(rows),documents=sorted({r['document'] for r in held}),excludedSharedChunks=[dict(document=r['document'],text=r['text']) for r in excluded],randomInitialization=random_control,frozenModel=frozen,note='Raw next-token objective on separate source pages. Complete passages were deduplicated before chunking; matching chunks after tokenization (including short common endings) are excluded here. Test articles never fit vocabulary, train weights or select checkpoints. This metric does not measure natural dialogue, facts or reasoning; different vocabularies are not directly compared.')
pathlib.Path(args.out).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
