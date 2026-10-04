"""Verify unmasked greedy recall of training-only sourced facts, in PyTorch.

This measures memorization in both styles and languages, not general knowledge.
Checkpoint input must be a trusted checkpoint produced by our local trainer.
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib

import torch

parser = argparse.ArgumentParser()
parser.add_argument('--corpus', required=True)
parser.add_argument('--model', required=True, help='Own exported model JS')
parser.add_argument('--checkpoint', help='Trusted local checkpoint; checks bestState')
parser.add_argument('--out')
args = parser.parse_args()
torch.set_num_threads(1)
spec = importlib.util.spec_from_file_location('trainer', pathlib.Path(__file__).with_name('train-transformer.py'))
trainer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trainer)
source = pathlib.Path(args.model).read_text()
exported = json.loads(source.split('export const neuralModel=', 1)[1].rstrip(';\n'))
model = trainer.Decoder(exported['config'])
step, best = None, None
if args.checkpoint:
    checkpoint = torch.load(args.checkpoint, weights_only=False)
    model.load_state_dict(checkpoint['bestState'])
    step, best = checkpoint['step'], checkpoint['bestStep']
else:
    model.load_state_dict({key: torch.tensor(value['data']).reshape(value['shape']) for key, value in exported['tensors'].items()})
model.eval()
corpus = json.loads(pathlib.Path(args.corpus).read_text())
rows = [row for row in corpus['rows'] if row.get('trainOnly')]
tokens = torch.tensor([row['tokens'][:row['prefixLength']] for row in rows])
generated = [[] for row in rows]
ended = [False for row in rows]
with torch.no_grad():
    for _ in range(exported['config']['context'] - tokens.shape[1]):
        next_ids = model(tokens)[:, -1].argmax(-1)
        for index, value in enumerate(next_ids.tolist()):
            if ended[index]:
                continue
            if value == 1:
                ended[index] = True
            else:
                generated[index].append(value)
        if all(ended):
            break
        tokens = torch.cat((tokens, next_ids[:, None]), dim=1)
failures = []
for index, row in enumerate(rows):
    target = row['tokens'][row['prefixLength']:-1]
    if not ended[index] or generated[index] != target:
        failures.append(dict(id=row['id'], generated=''.join(exported['vocabulary'][t] for t in generated[index]), ended=ended[index]))
report = dict(model=exported['version'], modelSha256=hashlib.sha256(source.encode()).hexdigest(), checkpointStep=step, bestStep=best, rows=len(rows), exact=len(rows)-len(failures), failures=failures, note='Unrestricted greedy decoding; known-fact memorization, not held-out factual generalization.')
if args.out:
    pathlib.Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(bool(failures))
