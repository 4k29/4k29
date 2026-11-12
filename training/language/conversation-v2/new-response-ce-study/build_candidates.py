"""Quarantine corpus audit. No training adoption, no text repair, no model calls."""
import pathlib,json,hashlib,sys,re,unicodedata,collections,difflib,time,os
P=pathlib.Path(__file__).resolve().parent;V=pathlib.Path(os.environ.get('CE_V2_ROOT',str(P.parent)));sys.path.insert(0,str(V));from new_tokenizer import Encoder
T=json.loads((V/'data/tokenizer.json').read_text());enc=Encoder(T);pieces=[bytes.fromhex(t)for t in T['bytes']]
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(s):return ''.join(unicodedata.normalize('NFKC',s).split()).casefold()
def objects(text):
 quote=False;escape=False;depth=0;start=None
 for i,c in enumerate(text):
  if quote:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c=='"':quote=False
  elif c=='"':quote=True
  elif c=='{':
   if depth==0:start=i
   depth+=1
  elif c=='}':
   depth-=1
   if depth==0:yield start,i+1,text[start:i+1]
 if quote or depth:raise ValueError('Unterminated source record; no guessed reconstruction')
rows=[];parse=[];rawstats={};seen={};dups=[]
for f in sorted((P/'PRIVATE').glob('ichikara*.json')):
 text=f.read_text();ok=bad=0
 for a,b,raw in objects(text):
  try:r=json.loads(raw);assert set(r)>={'ID','text','output'};assert isinstance(r['text'],str)and isinstance(r['output'],str)
  except (json.JSONDecodeError,AssertionError)as e:bad+=1;parse.append(dict(file=f.name,start_char=a,end_char=b,raw_sha256=sha(raw.encode()),error=str(e)));continue
  ok+=1;key=sha((r['text']+'\0'+r['output']).encode())
  if key in seen:dups.append(dict(file=f.name,id=r['ID'],same_as=seen[key]));continue
  seen[key]=f.name+':'+r['ID'];rows.append(dict(id=f.name+':'+r['ID'],original_id=r['ID'],source='ichikara',question=r['text'],answer=r['output'],origin=dict(file=f.name,start_char=a,end_char=b,raw_sha256=sha(raw.encode())),authorship='original publisher claims human Japanese writing; no individual author ID',rights='quarantine; NC research only, model-publication prohibition, original-package match pending'))
 rawstats[f.name]=dict(strict_valid_objects=ok,invalid_objects=bad)
for l in (P/'PRIVATE/instruction_ja.jsonl').read_text().splitlines():
 r=json.loads(l);us=r['utterances'];path=[s['path']for s in(r.get('original_info')or{}).get('sources',[])];out=[]
 for j,u in enumerate(us):
  assert u['name']in ['user','agent']
  out.append(u)
  if u['name']=='agent':rows.append(dict(id=r['id']+':'+str(j),original_id=r['id'],source='instruction_ja',history=out[:],question='\n'.join(z['text']for z in out[:-1]),answer=u['text'],authorship='model-origin English assistant, machine Japanese translation, human modification',upstream_test_reference=any('/test.'in s for s in path),upstream_sources=path,rights='MIT; all three notices required'))
# Group exact normalized question across all sources; every alternative answer stays together.
parent=list(range(len(rows)));find=lambda i: i if parent[i]==i else find(parent[i])
qs={};answers={};nearlinks=[]
for i,r in enumerate(rows):
 q=canon(r['question']);r['question_sha256']=sha(q.encode());a=canon(r['answer']);r['answer_sha256']=sha(a.encode());
 for mapping,key in [(qs,q),(answers,a)]:
  if key in mapping:parent[find(i)]=find(mapping[key])
  else:mapping[key]=i
# Conservative near-question unions from shared rare5-gram candidates; not semantic proof.
buckets=collections.defaultdict(list);checked=set()
for i,r in enumerate(rows):
 q=canon(r['question']);grams={q[j:j+5]for j in range(max(0,len(q)-4))};candidates=set()
 for g in grams:
  if len(buckets[g])<=30:candidates.update(buckets[g])
 for j in candidates:
  if (j,i)in checked:continue
  checked.add((j,i));p=canon(rows[j]['question'])
  if min(len(q),len(p))/max(len(q),len(p),1)>=.9 and difflib.SequenceMatcher(None,q,p,autojunk=False).ratio()>=.9:parent[find(i)]=find(j);nearlinks.append([rows[j]['id'],r['id']])
 for g in grams:buckets[g].append(i)
oldquestions=set();oldanswers=set()
for part in ['train','dev']:
 for l in (V/'data'/f'{part}.docs.jsonl').open():
  d=json.loads(l);us=d['utterances']
  for i,u in enumerate(us):
   oldanswers.add(canon(u['text']))
   if i+1<len(us):oldquestions.add(canon(u['text']))
stats=collections.defaultdict(collections.Counter);public=[]
for i,r in enumerate(rows):
 r['family']='qf:'+sha(rows[find(i)]['question'].encode());n=int(sha(('new-response-v1|'+r['family']).encode()),16)%10;r['partition']='dev'if n==0 else'train';q=enc(r['question']);a=enc(r['answer']);assert b''.join(pieces[t]for t in q)==r['question'].encode()and b''.join(pieces[t]for t in a)==r['answer'].encode();tokens=[1]
 if r['source']=='ichikara':tokens+=[3]+q+[2,4];s=len(tokens);tokens+=a+[2]
 else:
  for j,u in enumerate(r['history']):
   tokens+=[3 if u['name']=='user' else 4];s=len(tokens);tokens+=enc(u['text'])+[2]
 r.update(tokens=tokens,response_body_start=s,question_tokens=len(q),body_tokens=len(a),input_tokens=len(tokens)-1,roundtrip=True)
 flags=[]
 if len(tokens)>257:flags.append('complete_input_over_context256')
 if r.get('upstream_test_reference'):flags.append('upstream_public_TEST_reference_not_train')
 if canon(r['question'])in oldquestions:flags.append('exact_question_in_existing_RealPersona')
 if canon(r['answer'])in oldanswers:flags.append('exact_answer_in_existing_RealPersona')
 if re.search(r'https?://|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b0\d{1,3}-\d{2,4}-\d{3,4}\b',r['question']+r['answer']):flags.append('URL_email_phone_or_quote_needs_review')
 if not a or not q:flags.append('empty')
 r['mechanical_holds']=flags;r['mechanically_eligible']=not flags;r['training_authorized']=False
 st=stats[r['source']];st['unique_pairs']+=1;st['body_tokens_all']+=len(a);st['input_tokens_all']+=len(tokens)-1;st['families']+=0
 for f in flags:st[f]+=1
 if not flags:st[r['partition']+'_eligible_pairs']+=1;st[r['partition']+'_eligible_body_tokens']+=len(a)
 public.append({k:r[k]for k in ['id','source','family','partition','question_sha256','answer_sha256','question_tokens','body_tokens','input_tokens','mechanical_holds','mechanically_eligible','training_authorized','authorship']})
for source in stats:stats[source]['families']=len({r['family']for r in rows if r['source']==source})
(P/'PRIVATE/CANDIDATES.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n');(P/'CANDIDATE_METADATA.json').write_text(json.dumps(public,indent=2)+'\n');(P/'CORPUS_AUDIT.json').write_text(json.dumps(dict(files=rawstats,invalid_record_holds=parse,exact_duplicate_pairs_removed=len(dups),duplicates=dups,near_question_family_unions=len(nearlinks),sources={s:dict(z)for s,z in stats.items()},new_special_tokens=0,tokenizer_sha256=sha((V/'data/tokenizer.json').read_bytes()),all_UTF8_BPE_roundtrip=True,role_contract='new research mapping user3/assistant4; different semantics from old humanA/B, no vocabulary or architecture change; do not mix old RealPersona as assistant',training_authorized=False,optimizer_calls=0,model_forwards=0),indent=2)+'\n');print(json.dumps({s:dict(z)for s,z in stats.items()}));print('invalid',len(parse),'duplicates',len(dups),'nearlinks',len(nearlinks))
