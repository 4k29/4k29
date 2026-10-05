"""Independent numerical references for newly available own position rows.

Teacher-forced validation prefix is only a numerical parity input. It is never
provided to normal inference or used to choose weights/mark an answer correct.
"""
import argparse,hashlib,json,pathlib,torch
from train import DialogueDecoder
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--corpus',required=True);p.add_argument('--out',required=True);args=p.parse_args()
torch.set_num_threads(1)
file=pathlib.Path(args.model);e=json.loads(file.read_text().split('export const dialogueModel=',1)[1].strip().removesuffix(';'));c=json.loads(pathlib.Path(args.corpus).read_text())
assert e['training']['sourceSha256']==c['sourceSha256'] and e['tokenizer']==c['tokenizer']
model=DialogueDecoder(e['config']);model.load_state_dict({k:torch.tensor(t['data']).reshape(t['shape']) for k,t in e['tensors'].items()});model.eval()
row=max((r for r in c['rows'] if r['partition']=='validation'),key=lambda r:len(r['tokens']))
assert len(row['tokens'])>300
refs=[]
with torch.no_grad():
 for length in [255,257,len(row['tokens'])-2]:
  tokens=row['tokens'][:length];refs.append(dict(id=row['id']+':numerical-prefix:'+str(length),tokens=tokens,logits=model(torch.tensor([tokens]))[0,-1].tolist(),containsApprovedGoldPrefix=True))
result=dict(version=e['version'],sourceSha256=c['sourceSha256'],modelFileSha256=hashlib.sha256(file.read_bytes()).hexdigest(),scope='Numerical validation only. Independent PyTorch full-prefix computation at255,257,and longest VALID prefix, with rounded exported own weights. Includes approved gold answer tokens only to reach trained late positions; not an accuracy test, runtime answer assistance or weight selector.',references=refs)
pathlib.Path(args.out).write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps({'version':e['version'],'references':[len(r['tokens']) for r in refs]}))
