"""Evaluate frozen own dialogue weights on never-trained question families.

The test partition is read only here, after checkpoint selection is complete.
"""
import argparse
import json
import pathlib
import torch
from train import DialogueDecoder,generate
from tokenizer import encode,prompt,SPECIALS

parser=argparse.ArgumentParser()
parser.add_argument('--model',required=True)
parser.add_argument('--corpus',default=str(pathlib.Path(__file__).with_name('corpus.json')))
parser.add_argument('--out',required=True)
parser.add_argument('--partition',choices=['train','validation','test'],default='test')
args=parser.parse_args()
torch.set_num_threads(1)
source=pathlib.Path(args.model).read_text()
exported=json.loads(source.split('export const dialogueModel=',1)[1].strip().removesuffix(';'))
corpus=json.loads(pathlib.Path(args.corpus).read_text())
model=DialogueDecoder(exported['config'])
model.load_state_dict({key:torch.tensor(t['data']).reshape(t['shape']) for key,t in exported['tensors'].items()})
rows=[];overflow=[]
for original in corpus['rows']:
    if original['partition']!=args.partition:continue
    # Each frozen model has its own learned tokenizer. Comparing models must
    # encode and decode with that model, never reuse another vocabulary's IDs.
    row=dict(original)
    prefix=prompt(row['question'],row['history'],exported['tokenizer'])
    row['prefixLength']=len(prefix)
    row['tokens']=prefix+encode(row['answer'],exported['tokenizer'])+[SPECIALS['eos']]
    if len(prefix)>=exported['config']['context']:
        overflow.append(dict(id=row['id'],kind=row['kind'],question=row['question'],history=row['history'],expected=row['answer'],answer=None,exact=False,eos=False,validTokens=False,error='context-overflow'))
    else:rows.append(row)
outputs=generate(model,rows,exported['tokenizer'])+overflow
kinds=sorted({r['kind'] for r in outputs})
unknown=[r for r in outputs if r['kind']=='unknown']
unknown_replies=['その情報は分かりません。','すみません、よく分かりません']
clean=lambda text:str(text or '').strip().rstrip('。.!！')
boundary=dict(total=len(unknown),abstained=sum(clean(r['answer']) in {clean(t) for t in unknown_replies} for r in unknown),acceptedWording=unknown_replies)
report=dict(version=exported['version'],training=exported['training'],partition=args.partition,sourceSha256=corpus.get('sourceSha256'),total=len(outputs),exact=sum(r['exact'] for r in outputs),contextOverflows=len(overflow),unsupportedBoundary=boundary,byKind={kind:dict(total=sum(r['kind']==kind for r in outputs),exact=sum(r['kind']==kind and r['exact'] for r in outputs)) for kind in kinds},rows=outputs,note='Unconstrained full-answer argmax using the evaluated model\'s own tokenizer. Exact wording is strict and not the same as factual/semantic correctness. Unknown boundaries also accept the authorized previous unknown wording. Test families never fit the new curriculum or select its checkpoints; reused legacy test families remain development diagnostics. This finite authored test is not a general language benchmark.')
pathlib.Path(args.out).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key not in ['rows','training']},ensure_ascii=False))
