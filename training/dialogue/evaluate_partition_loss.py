"""Post-selection diagnostic on every authored QA target, not chat quality.

Training rows and validation rows cover different question/pair distributions.
Teacher-forced loss cannot establish complete, factual or fluent generation.
"""
import argparse
import collections
import json
import pathlib
import torch
from torch.nn import functional as F
from train import DialogueDecoder,pack
from tokenizer import SPECIALS

p=argparse.ArgumentParser()
p.add_argument('--model',required=True)
p.add_argument('--corpus',required=True)
p.add_argument('--out',required=True)
args=p.parse_args()
torch.set_num_threads(1)
exported=json.loads(pathlib.Path(args.model).read_text().split('export const dialogueModel=',1)[1].strip().removesuffix(';'))
corpus=json.loads(pathlib.Path(args.corpus).read_text())
if exported['training']['sourceSha256']!=corpus['sourceSha256']:raise ValueError('Model/source mismatch')
model=DialogueDecoder(exported['config'])
model.load_state_dict({k:torch.tensor(v['data']).reshape(v['shape']) for k,v in exported['tensors'].items()})
model.eval()
groups=collections.defaultdict(list)
for row in corpus['rows']:groups[(row['partition'],row['kind'])].append(row)
details=[]
with torch.no_grad():
    for (partition,kind),rows in sorted(groups.items()):
        ordered=sorted(rows,key=lambda r:len(r['tokens']))
        total,tokens=0.0,0
        for start in range(0,len(ordered),32):
            batch=ordered[start:start+32]
            x,y=pack(batch,SPECIALS['pad'],max(len(r['tokens'])-1 for r in batch))
            total+=F.cross_entropy(model(x).reshape(-1,exported['config']['vocabulary']),y.reshape(-1),reduction='sum').item()
            tokens+=y.ne(-100).sum().item()
        assert tokens==sum(len(r['tokens'])-r['prefixLength'] for r in rows)
        details.append(dict(partition=partition,kind=kind,rows=len(rows),targetTokens=tokens,nllSum=total,loss=total/tokens))
partitions={}
for partition in ['train','validation','test']:
    selected=[r for r in details if r['partition']==partition]
    tokens=sum(r['targetTokens'] for r in selected)
    partitions[partition]=dict(rows=sum(r['rows'] for r in selected),targetTokens=tokens,loss=sum(r['nllSum'] for r in selected)/tokens)
report=dict(version=exported['version'],sourceSha256=corpus['sourceSha256'],partitions=partitions,byKind=details,note='Unsmoothed teacher-forced target-token loss on all QA rows after checkpoint selection. trainLoss in the training log covers only its first 256 rows; this report covers the entire partition. Train/validation/test question and arithmetic distributions differ, so their gap alone does not isolate overfitting. Low target loss does not establish correct unconstrained generation. No new audit rows are used here.')
pathlib.Path(args.out).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(version=report['version'],partitions=partitions),ensure_ascii=False))
