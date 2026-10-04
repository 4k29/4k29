"""Compare own checkpoints on identical held-out grammar groups.

No model is trained here. Literal training-only rows are excluded. Validation
is development grammar data, not a test of open-ended conversational ability.
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib

import torch
from torch.nn import functional as F

parser = argparse.ArgumentParser()
parser.add_argument('--models', nargs='+', required=True)
parser.add_argument('--corpora', nargs='+', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()
torch.set_num_threads(1)
spec = importlib.util.spec_from_file_location('trainer', pathlib.Path(__file__).with_name('train-transformer.py'))
trainer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trainer)
results = []
for filename in args.models:
    raw = pathlib.Path(filename).read_bytes()
    exported = json.loads(raw.decode().split('export const neuralModel=', 1)[1].strip().removesuffix(';'))
    model = trainer.Decoder(exported['config'])
    model.load_state_dict({key: torch.tensor(value['data']).reshape(value['shape']) for key, value in exported['tensors'].items()})
    model.eval()
    partitions = []
    for corpusname in args.corpora:
        corpus = json.loads(pathlib.Path(corpusname).read_text())
        if corpus['vocabulary'] != exported['vocabulary']:
            raise ValueError('Vocabulary differs: '+corpusname)
        rows = [row for row in corpus['rows'] if not row.get('trainOnly') and int(hashlib.sha256(row['group'].encode()).hexdigest()[:8],16)%7==0]
        width = max(len(row['tokens'])-1 for row in rows)
        tokens = torch.full((len(rows),width),corpus['pad'],dtype=torch.long)
        targets = torch.full_like(tokens,-100)
        for index,row in enumerate(rows):
            length=len(row['tokens'])-1
            tokens[index,:length]=torch.tensor(row['tokens'][:-1])
            targets[index,:length]=torch.tensor(row['tokens'][1:])
            targets[index,:row.get('prefixLength',4)-1]=-100
        total,count=0.0,0
        with torch.no_grad():
            for start in range(0,len(rows),64):
                y=targets[start:start+64]
                total+=F.cross_entropy(model(tokens[start:start+64]).reshape(-1,len(corpus['vocabulary'])),y.reshape(-1),reduction='sum').item()
                count+=y.ne(-100).sum().item()
        partitions.append(dict(corpus=corpusname,sourceSha256=corpus['sourceSha256'],rows=len(rows),tokens=count,loss=total/count))
    results.append(dict(model=filename,version=exported['version'],sha256=hashlib.sha256(raw).hexdigest(),partitions=partitions))
report=dict(results=results,note='Identical SHA-256 held-out grammar groups, token-weighted cross entropy. Development validation, not general Japanese or factual accuracy.')
pathlib.Path(args.out).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
