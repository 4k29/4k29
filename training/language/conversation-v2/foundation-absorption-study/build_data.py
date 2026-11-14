"""Prior bounded research prose only. No new network corpus, no FAQ answers in LM."""
import pathlib,json,gzip,sys,hashlib,re,collections,unicodedata,os
P=pathlib.Path(__file__).resolve().parent;assert not(P/'PLAN.json').exists(),'Do not overwrite frozen study; rebuild in a new directory';V=P.parent;CACHE=pathlib.Path(os.environ.get('ABSORPTION_CACHE','/workspace/scratch/absorption'));sys.path.insert(0,str(V));from new_tokenizer import Encoder
enc=Encoder(json.loads((V/'data/tokenizer.json').read_text()));pieces=[bytes.fromhex(x)for x in json.loads((V/'data/tokenizer.json').read_text())['bytes']];sha=lambda b:hashlib.sha256(b).hexdigest();load=lambda n:json.loads(gzip.decompress((CACHE/n).read_bytes()));lines=lambda n:[json.loads(x)for x in gzip.decompress((CACHE/n).read_bytes()).splitlines()];canon=lambda s:''.join(unicodedata.normalize('NFKC',s).split());fold=lambda s:re.sub(r'\n{2,}','\n',s)
faq=json.loads((V/'faq-ce-verified-study/DATA.json').read_text());fa=faq['parts']['train']+faq['parts']['dev'];refs=[canon(x[k])for x in fa for k in['question','response']];refs=[x for x in refs if len(x)>=16];furls={x['url'].split('#')[0].rstrip('/')for x in fa};old=load('mixed-retention-study/corpus.json.gz');seen={x['id']for x in old};div=lines('diverse-foundation/corpus.jsonl.gz');env=[x for x in lines('paragraph-foundation/corpus.jsonl.gz')if x['source']=='env_whitepaper'];rows=[];held=collections.Counter()
for x in div+env+ [x for x in lines('paragraph-foundation/corpus.jsonl.gz') if x['source']=='stair_unused_annotation']:
 s=x['source']
 if s not in['jaquad','jawikibooks','env_whitepaper','realpersona','stair_unused_annotation']:continue
 if x.get('split','train')!='train':continue
 if x['id']in seen:held['MIX579_record_already_selected']+=1;continue
 if s=='jawikibooks'and not x['provenance'].get('latestRevisionBefore2022',False):held['books_post2021_authorship_uncertainty']+=1;continue
 if x['source']=='jaquad'and (re.search('戦役|戦争|聖書|教会|キリスト',x['text'])or len(re.findall(r'[12][0-9]{3}年',x['text']))>=3):held['war_religious_reference_or_date_list']+=1;continue
 if x['source']=='jawikibooks'and x['id'].startswith('jawikibooks:19758:'):held['biology_chapter_factual_quality_hold']+=1;continue
 title=x.get('title',x.get('heading',''));text=fold(x['text']);c=canon(text)
 if re.search(r'法令|法学|憲法|戦争|大戦|歴史|アセンブリ|C言語|プログラミング|分子生物|有機化学',title):held['genre_risk_title']+=1;continue
 if s not in ['realpersona','stair_unused_annotation']and (text.count('。')<2 or not text.rstrip().endswith(('。','）',')'))):held['insufficient_contiguous_sentences']+=1;continue
 if len(re.findall('[0-9０-９]',text))/max(1,len(text))>.12 or len(re.findall('[a-zA-Z]',text))/max(1,len(text))>.18:held['numeric_latin_dominance']+=1;continue
 if re.search(r'「[^」]{50,}」|https?://|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',text):held['long_quotation_or_contact']+=1;continue
 url=x.get('source_url',x.get('provenance',{}).get('url','')).split('#')[0].rstrip('/')
 if url in furls or any(q in c or c in q for q in refs):held['FAQ_original_URL_or_substring']+=1;continue
 ts=[t for i,t in enumerate(x['tokens'])if not(t==16 and i and x['tokens'][i-1]==16)]if s=='realpersona'else ([1]if x.get('BOS')else[])+enc(text)+([2]if x.get('EOS')else[])
 if not (8 if s=='stair_unused_annotation'else 80)<=len(ts)<=1800:held['length']+=1;continue
 assert b''.join(pieces[t]for t in ts if t>=6)==(fold(''.join(u['text']for u in x['utterances']))if s=='realpersona'else text).encode();assert not any(a==b==16 for a,b in zip(ts,ts[1:]));assert bool(ts[-1]==2)==bool(x.get('EOS'))
 y={k:v for k,v in x.items()if k not in['tokens','body_tokens','text']};y.update(text=text,tokens=ts,original_text_sha256=sha(x['text'].encode()),text_sha256=sha(text.encode()),original_tokens_sha256=sha(json.dumps(x['tokens'],separators=(',',':')).encode()),transform='LF2+ to LF1 only; original order and true EOS/BOS preserved',prior_history='Wiki pool all selected PR105; ENV not selected by MIX579 record IDs; not globally new original data',source=s);rows.append(y)
# Exact full-body duplicates; near matching is separately audited before freeze.
unique={};dups=[]
for x in sorted(rows,key=lambda x:sha(('base-body-v1|'+x['id']).encode())):
 c=canon(x['text'])
 if c in unique:dups.append(x['id']);continue
 unique[c]=x
rows=list(unique.values());caps={'jaquad':650000,'env_whitepaper':180000,'jawikibooks':20000,'realpersona':50000,'stair_unused_annotation':100000};selected=[];counts=collections.Counter()
for x in rows:
 n=sum(t>=6 and t!=16 for t in x['tokens'][1:])
 if counts[x['source']]+n>caps[x['source']]:continue
 selected.append(x);counts[x['source']]+=n
selected.sort(key=lambda x:sha(('base-order-v1|'+x['id']).encode()));batches=[];windows=[]
for k,x in enumerate(selected):
 t=x['tokens']
 for start in range(1,len(t),192):
  end=min(len(t),start+192);a=max(0,end-257);windows.append(dict(record=k,input_start=a,target_start=start,end=end,targets=end-start))
buckets=collections.defaultdict(list)
for w in windows:buckets[(w['end']-w['input_start']-2)//32].append(w)
batches=[]
for key,ws in sorted(buckets.items()):
 batch=[];active=0;maxlen=0
 for w in ws:
  n=w['end']-w['input_start']-1
  if batch and (active+w['targets']>1024 or (len(batch)+1)*max(maxlen,n)>4096 or len(batch)>=48):batches.append(batch);batch=[];active=0;maxlen=0
  batch.append(w);active+=w['targets'];maxlen=max(maxlen,n)
 if batch:batches.append(batch)
batches.sort(key=lambda b:sha(('LM-batch-order-v1|'+json.dumps(b,separators=(',',':'))).encode()));sample=[]
for s in caps:
 a=[x for x in selected if x['source']==s];a.sort(key=lambda x:sha(('quality-fixed-v1|'+x['id']).encode()));sample+=a[:8]
# New continuation prefixes on existing source-held-out official paragraphs. Not new TEST.
dev=[]
for x in div:
 if x['split']!='dev'or x['text'].count('。')<3:continue
 if x.get('provenance',{}).get('url','').rstrip('/')in furls:continue
 text=fold(x['text']);ts=([1]if x['BOS']else[])+enc(text)+([2]if x['EOS']else[]);end=text.find('。')+1;raw=text[:end].encode();prefix_bytes=b'';cut=None
 for i,t in enumerate(ts):
  prefix_bytes+=pieces[t]
  if prefix_bytes==raw:cut=i+1;break
  if len(prefix_bytes)>len(raw):break
 if cut is None or not 12<=cut<=112:continue
 if len(ts)-cut<24:continue
 dev.append(dict(**{k:x[k]for k in ['id','source','family','text','provenance']},tokens=ts,prefix=ts[:cut],maxNewTokens=min(128,256-cut),teacher_continuation=ts[cut:cut+min(32,len(ts)-cut)],rubric='Topic/objects from prefix retained, new coherent2–3 sentences with causal/referential connection, no harmful repetition; correct paraphrase allowed; token match not required',already_exposed_DEV=True))
assert len(dev)>=6
write=lambda n,x:(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
(P/'corpus.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))for x in selected)+'\n').encode(),mtime=0));write('SCHEDULE.json',dict(batches=batches,one_pass=True,stride=192,max_input=256,targets=sum(x['targets']for x in windows),body_nonLF_targets=sum(counts.values()),unique_original_records=len(selected)));write('PROSE_DEV.json',dict(cases=dev,selection='all eligible prior source-heldout JMA sections with exact-token first-sentence boundary, >=3sentences; not newly unexposed TEST',sealed_TEST=False));write('QUALITY_SAMPLE.json',dict(seed='quality-fixed-v1',cases=[{k:x[k]for k in['id','source','text','family']}for x in sample]));write('SOURCE_AUDIT.json',dict(source_nonLF_body_targets=dict(counts),pool_eligible=collections.Counter(x['source']for x in rows),eligible_body=collections.Counter({s:sum(sum(t>=6 and t!=16 for t in x['tokens'][1:])for x in rows if x['source']==s)for s in caps}),held=dict(held),exact_duplicates=dups,all_selected_records_not_in_MIX579=True,globally_unseen_Wiki_body_targets=0,prior_Wiki_PR105_exposure=True,new_network_corpus_acquisition=0,FAQ_substring_URL_cross=0,DEV_families=list(sorted({x['family']for x in dev})),source_archive_SHA={n:sha((CACHE/n).read_bytes())for n in['diverse-foundation/corpus.jsonl.gz','paragraph-foundation/corpus.jsonl.gz','mixed-retention-study/corpus.json.gz']},human_authorship='Inherited bounded exploratory admission, wiki contributors human/bot not fully verifiable; pre2022 Books only. No assertion of human-only corpus',admission='Bounded exploratory, not formal corpus/model adoption'))
print('selected',len(selected),'body',dict(counts),'updates',len(batches),'teachers',sum(w['targets']for w in windows),'DEV',len(dev),'sample',len(sample))
