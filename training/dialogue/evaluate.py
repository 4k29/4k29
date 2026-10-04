"""Evaluate frozen own dialogue weights on never-trained question families.

The test partition is read only here, after checkpoint selection is complete.
"""
import argparse
import json
import pathlib
import torch
from train import DialogueDecoder,generate

parser=argparse.ArgumentParser()
parser.add_argument('--model',required=True)
parser.add_argument('--corpus',default=str(pathlib.Path(__file__).with_name('corpus.json')))
parser.add_argument('--out',required=True)
args=parser.parse_args()
torch.set_num_threads(1)
source=pathlib.Path(args.model).read_text()
exported=json.loads(source.split('export const dialogueModel=',1)[1].strip().removesuffix(';'))
corpus=json.loads(pathlib.Path(args.corpus).read_text())
model=DialogueDecoder(exported['config'])
model.load_state_dict({key:torch.tensor(t['data']).reshape(t['shape']) for key,t in exported['tensors'].items()})
rows=[row for row in corpus['rows'] if row['partition']=='test']
outputs=generate(model,rows,corpus['tokenizer'])
kinds=sorted({r['kind'] for r in rows})
report=dict(version=exported['version'],training=exported['training'],total=len(outputs),exact=sum(r['exact'] for r in outputs),byKind={kind:dict(total=sum(r['kind']==kind for r in outputs),exact=sum(r['kind']==kind and r['exact'] for r in outputs)) for kind in kinds},rows=outputs,note='Entire answer generated with unconstrained argmax from question/history tokens. Test question families and arithmetic operand pairs were never trained or used to select weights. All labels/answers are finite authored or exact synthetic data; this is not a general language benchmark.')
pathlib.Path(args.out).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key not in ['rows','training']},ensure_ascii=False))
