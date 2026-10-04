"""Diagnostic only: can the training-only heads identify subject and field?

Gold semantic labels come from unambiguous approved training targets matching
the authored audit gold answer. Nothing here supplies or modifies generation.
Ambiguous labels and new reasoning answers are excluded, never guessed.
"""
import argparse
import collections
import json
import pathlib
import torch
from train import DialogueDecoder
from tokenizer import prompt
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--corpus',required=True);p.add_argument('--audit',required=True);p.add_argument('--out',required=True);args=p.parse_args()
torch.set_num_threads(1)
exported=json.loads(pathlib.Path(args.model).read_text().split('export const dialogueModel=',1)[1].strip().removesuffix(';'))
corpus=json.loads(pathlib.Path(args.corpus).read_text());audit=json.loads(pathlib.Path(args.audit).read_text())
if corpus['sourceSha256']!=exported['training']['sourceSha256']:raise ValueError('Model/source mismatch')
labels=exported['config']['semanticTasks'];targets=collections.defaultdict(set)
for r in corpus['rows']:
    if r['partition']=='train':targets[r['answer']].add(tuple(r['semantic'][name] for name in labels))
model=DialogueDecoder(exported['config']);model.load_state_dict({k:torch.tensor(v['data']).reshape(v['shape']) for k,v in exported['tensors'].items()});model.eval()
rows=[];excluded=[]
with torch.no_grad():
    for r in audit['rows']:
        candidates=targets[r['answer']]
        if len(candidates)!=1:excluded.append(dict(id=r['id'],question=r['question'],reason='unavailable-or-ambiguous-semantic-gold'));continue
        expected=dict(zip(labels,next(iter(candidates))))
        tokens=prompt(r['question'],r['history'],exported['tokenizer'])
        _,heads=model(torch.tensor([tokens]),semantic_positions=torch.tensor([len(tokens)-1]))
        actual={name:labels[name][head[0].argmax().item()] for name,head in heads.items()}
        rows.append(dict(id=r['id'],question=r['question'],history=r['history'],expected=expected,actual=actual,exact=actual==expected))
report=dict(version=exported['version'],sourceSha256=corpus['sourceSha256'],auditSha256=audit['sourceSha256'],total=len(rows),bothCorrect=sum(r['exact'] for r in rows),byTask={name:sum(r['expected'][name]==r['actual'][name] for r in rows) for name in labels},rows=rows,excluded=excluded,note='Training-only question-boundary head diagnostic. It neither supplies answers nor participates in inference/checkpoint selection; it is not dialogue correctness.')
pathlib.Path(args.out).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['rows','excluded']},ensure_ascii=False))
