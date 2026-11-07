"""TRAIN-only matched-length context diagnostic, no optimization or TEST reads."""
import argparse,hashlib,importlib.util,json,pathlib,sys,re
R=pathlib.Path(__file__).resolve().parents[1]; PRE=R.parent/'round40'; E=R/'execution'
sys.path.insert(0,str(R.parent/'round10'))
s=importlib.util.spec_from_file_location('evaluation',R.parent/'round10/evaluate.py');ev=importlib.util.module_from_spec(s);s.loader.exec_module(ev)
sha=lambda b:hashlib.sha256(b).hexdigest()
def prepare(auxiliary=False):
 tok=json.loads((PRE/'multiview/tokenizer.json').read_text());docs=[]
 with (PRE/'sources/documents.jsonl').open() as f:
  for line in f:
   d=json.loads(line)
   if d['id'].startswith('realpersona:'):docs.append(d)
 docs.sort(key=lambda d:sha(('r40-context-v1:'+d['id']).encode()))
 candidates=[]
 for d in docs[:512]:
  assert d['partition']=='train'
  raw=(pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train')/pathlib.Path(d['sourcePath']).name).read_bytes();assert sha(raw)==d['sourceSha256']
  turns=[x['text'] for x in json.loads(raw)['utterances']];assert '\n'.join(turns)==d['text']
  # Original utterance objects retain embedded newlines. Re-encoding is diagnostic only.
  for j in range(2,len(turns)):
   prefix='\n'.join(turns[j-2:j])+'\n';target=turns[j];p=ev.encode_stream(prefix,tok);t=ev.encode_stream(target,tok)
   if 16<=len(p)<=96 and 12<=len(t)<=96 and ev.encode_stream(prefix+target,tok)==p+t:
    candidates.append(dict(document=d['id'],sourceSha256=d['sourceSha256'],sourcePath=d['sourcePath'],turn=j,prefix=prefix,target=target,prefixTokens=p,targetTokens=t))
 candidates.sort(key=lambda d:sha(('r40-pair-v1:'+d['document']+':'+str(d['turn'])).encode()))
 buckets={}
 for c in candidates:buckets.setdefault(len(c['prefixTokens']),[]).append(c)
 pairs=[];used=set()
 for c in candidates:
  if c['document'] in used:continue
  anchors=sorted(set(re.findall(r'[一-龯]{2,}',c['target'])) & set(re.findall(r'[一-龯]{2,}',c['prefix'])))
  if auxiliary and not anchors:continue
  wrong=next((x for x in buckets[len(c['prefixTokens'])] if (not auxiliary or not any(z in x['prefix'] for z in anchors)) and x['document']!=c['document'] and x['prefix']!=c['prefix'] and x['target']!=c['target'] and ev.encode_stream(x['prefix']+c['target'],tok)==x['prefixTokens']+c['targetTokens']),None)
  if wrong is None:continue
  pairs.append(dict(**c,wrongDocument=wrong['document'],wrongSourceSha256=wrong['sourceSha256'],wrongTurn=wrong['turn'],wrongPrefix=wrong['prefix'],wrongPrefixTokens=wrong['prefixTokens']));used.add(c['document']) if not auxiliary else None
  if len(pairs)==64 and not auxiliary:break
 assert len(pairs)>=64
 report=dict(partition='TRAIN ONLY: RealPersona original human utterances',trainingUpdates=0,reservedTestRead=False,usedForCheckpointSelection=False,limitations=['Teacher-forced context sensitivity is not semantic generation ability','Random mismatches can be valid responses; these are NOT audited negative training labels','Canonical re-encoding of complete two-turn prefix and original next utterance; no EOS appended'],selection=('Original full human targets with an identical maximal >=2-kanji run in true context and target, absent from different-document same-length donor; all eligible pairs, not semantic negative labels' if auxiliary else '512 documents sorted salted SHA; 64 distinct positive documents sorted salted pair SHA; first different-document same-token-length donor; no model scores used'),sourceDocumentsSha256=sha((PRE/'sources/documents.jsonl').read_bytes()),tokenizerSha256=sha((PRE/'multiview/tokenizer.json').read_bytes()),rows=pairs)
 dest=E/('context-auxiliary-pool.json' if auxiliary else 'context-plan.json');assert not dest.exists();dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('frozen TRAIN pairs',len(pairs),sha(dest.read_bytes()),flush=True)
def evaluate(path,out):
 ev.torch.set_num_threads(1);raw=(E/'context-plan.json').read_bytes();plan=json.loads(raw);cp=ev.torch.load(path,map_location='cpu',weights_only=False);model=ev.Decoder(cp['config']);model.load_state_dict(cp['model']);model.eval();rows=[]
 with ev.torch.no_grad():
  for i,r in enumerate(plan['rows']):
   scores=[]
   for key in ['prefixTokens','wrongPrefixTokens']:
    p=[ev.SPECIALS['bos']]+r[key];t=r['targetTokens'];seq=p+t
    logits=model(ev.torch.tensor([seq[:-1]]))[0,len(p)-1:];loss=ev.torch.nn.functional.cross_entropy(logits,ev.torch.tensor(t),reduction='sum');scores.append(float(loss)/len(t))
   rows.append(dict(index=i,document=r['document'],correctNllPerToken=scores[0],mismatchedNllPerToken=scores[1],contextGain=scores[1]-scores[0]))
 report=dict(planSha256=sha(raw),modelSha256=sha(path.read_bytes()),checkpointStep=cp['step'],trainingUpdates=0,partition=plan['partition'],reservedTestRead=False,usedForCheckpointSelection=False,meanContextGain=sum(r['contextGain'] for r in rows)/len(rows),positiveContextGain=sum(r['contextGain']>0 for r in rows),pairs=len(rows),rows=rows)
 out.write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='rows'},flush=True)
p=argparse.ArgumentParser();p.add_argument('operation',choices=['prepare','prepare-auxiliary','evaluate']);p.add_argument('--model',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path);a=p.parse_args()
if a.operation.startswith('prepare'):prepare(a.operation=='prepare-auxiliary')
else:evaluate(a.model,a.out)
