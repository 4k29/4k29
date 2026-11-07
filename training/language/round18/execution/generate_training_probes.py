"""Posthoc TRAIN-only autoregressive diagnostic; no gate/selection/teacher use."""
import pathlib,json,hashlib,sys,re,subprocess,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
sys.path.insert(0,str(R.parent/'round10'));from evaluate import load_model,generate
from tokenizer import SPECIALS,encode_stream
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
p=read(E/'train-probe-policy.json');assert read(R/'continue-10000/result.json')['completedSteps']==10000
assert sha(R/'sources/documents.jsonl')==p['sourceDocumentsSha256'];source={d['id']:d for d in [json.loads(l) for l in (R/'sources/documents.jsonl').read_text().splitlines()]};torch.set_num_threads(1);reports={};statuses={}
for name,path in [('old',R.parent/'round16/continue-10000/model.js'),('new',R/'continue-10000/model.js')]:
 model,export=load_model(path);rows=[];refs=[]
 for x in p['rows']:
  d=source[x['document']];assert d['partition']=='train' and d['text'].startswith(x['prefix'])
  # Only the opening enters model generation. Expected prose is used below for diagnostics.
  raw=generate(model,x['prefix'],export['tokenizer'],p['maxNewTokens']);joined=x['prefix']+raw['text'];common=0
  for a,b in zip(joined,d['text']):
   if a!=b:break
   common+=1
  rows.append(dict(**x,**raw,matchingOriginalPrefixCharacters=common,exactOriginalDocumentCompletion=joined==d['text'] and raw['eos']))
  ts=[SPECIALS['bos']]+encode_stream(x['prefix'],export['tokenizer'])
  with torch.no_grad():logits=model(torch.tensor([ts]))[0,-1].tolist()
  refs.append(dict(id=x['id'],tokens=ts,logits=logits))
 g=dict(modelFileSha256=sha(path),policySha256=sha(E/'train-probe-policy.json'),partition='posthoc TRAIN diagnostic',maxNewTokens=192,evaluationThreads=1,usedForSelection=False,unseen=False,rows=rows,references=refs);write(E/f'{name}-train-generations.json',g);reports[name]=g
 result=subprocess.run(['node',str(R.parent/'round10/evaluate_js.mjs'),str(path),str(E/f'{name}-train-generations.json'),str(E/f'{name}-train-generations-js.json')],capture_output=True,text=True);(E/f'{name}-train-parity.log').write_text(result.stdout+result.stderr);statuses[name]=result.returncode
write(E/'train-probe-parity-status.json',statuses)
text=['# Posthoc TRAIN raw generations — not unseen or language-gate evidence','',f"Frozen at logged{p['lastLoggedStepAtFreeze']} before generation, after training started. Old/new greedy full vocabulary, max192, true EOS, Python1thread. No source lookup enters generation, no output repair. These three short TRAIN sources are excluded from gate and weight/hyperparameter selection.",'']
for x in p['rows']:
 text.extend(['## '+x['id'],'',x['url'],'','Opening:','','```text',x['prefix'],'```',''])
 for name,g in reports.items():
  row=next(r for r in g['rows'] if r['id']==x['id']);fence='`'*max(3,max((len(t) for t in re.findall('`+',row['text'])),default=0)+1);text.extend([name+' full continuation:','',fence+'text',row['text'],fence,''])
(E/'TRAIN_GENERATIONS.md').write_text('\n'.join(text)+'\n');print(json.dumps({n:dict(exactTrainDocumentCopies=sum(r['exactOriginalDocumentCompletion'] for r in g['rows']),parityExit=statuses[n]) for n,g in reports.items()}))
