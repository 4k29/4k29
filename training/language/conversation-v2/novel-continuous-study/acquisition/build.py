import os
"""Build genuinely new family corpus; no model forward, no generated text."""
import pathlib,sys,json,gzip,re,hashlib,unicodedata,collections,statistics,ipaddress
from extract import extract
C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'));V=pathlib.Path(__file__).resolve().parents[2];P=V/'novel-continuous-study';assert not(P/'PLAN.json').exists();sys.path.insert(0,str(V));from new_tokenizer import Encoder
enc=Encoder(json.loads((V/'data/tokenizer.json').read_text()));pieces=[bytes.fromhex(x)for x in json.loads((V/'data/tokenizer.json').read_text())['bytes']];h=lambda b:hashlib.sha256(b).hexdigest();canon=lambda s:''.join(unicodedata.normalize('NFKC',s).split());write=lambda n,v:(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sel=json.loads((P/'ACQUISITION_SELECTION.json').read_text());old=json.loads((C/'PRIOR_INDEX.json').read_text());reserved=json.loads((P/'DEV_RESERVED_FAMILIES.json').read_text());refs=json.loads((V/'faq-ce-verified-study/DATA.json').read_text());refrows=refs['parts']['train']+refs['parts']['dev'];reftext=[canon(r[k])for r in refrows for k in ['question','response']if len(canon(r[k]))>=8];reftext +=[canon(r['text'])for r in json.loads((P/'NEW_PROSE_DEV.json').read_text())['cases']];prior=json.loads(gzip.decompress((C/'PRIOR_TEXTS.json.gz').read_bytes()));priorcanon={canon(r['text'])for r in prior};priorroots={k:{r['title'].split('/')[0]for r in v.values()}for k,v in old.items()};priorids={k:{int(x.split(':')[1])for x in v if x.split(':')[1].isdigit()}for k,v in old.items()}
held=collections.Counter();rows=[];acquired=collections.Counter();pages=collections.Counter();seen=set();raw_shas={}
for site,ss in sel['selected_pages'].items():
 key='jawikibooks'if'books'in site else'jawikivoyage'
 for x in ss:
  f=C/'train-raw'/(site+'-'+str(x['pageid'])+'.json')
  if not f.exists():held[site+':not_acquired']+=1;continue
  obj=json.loads(f.read_text());pages[site]+=1;rev=obj['revision']
  if not rev:held[site+':no_pre2022_revision']+=1;continue
  raw_shas[f.name]=h(f.read_bytes())
  if x['title'].split('/')[0]in priorroots[key]or x['pageid']in priorids[key]:held['previous_family']+=1;continue
  if re.search(r'経済活動と法|政治経済|社会 公民|保健|医学|看護|病気|健康|治療|薬|教科書購入',x['title']):held['medical_legal_political_primary_topic']+=1;continue
  if re.search('bot',rev.get('user',''),re.I):held['last_editor_bot_uncertain']+=1;continue
  for r in extract(obj):
   acquired[site]+=len(enc(r['text']));s=r['text'];c=canon(s)
   if re.search(r'お前|馬鹿|バカ|死ね|キチガイ|頭が悪|劣等|発達障害|精神病|自殺|万引|死刑|性交|性感染|癌|がん治療|ダイエット|診断|電話|住所|メール',s):held['sensitive_or_abusive_or_contact']+=1;continue
   if re.search(r'図[0-9０-９]|上図|下図|右図|左図|次の図|前述|上述|前節|この図|ここを|下記|以下の表|上記|この表',s):held['missing_reference']+=1;continue
   if c in priorcanon or c in seen:held['exact_prior_or_internal']+=1;continue
   if any(q in c or c in q for q in reftext):held['FAQ_or_DEV_exact_substring']+=1;continue
   ts=[1]+enc(s)
   if not 80<=len(ts)<=1800:held['BPE_length']+=1;continue
   assert b''.join(pieces[t]for t in ts if t>=6)==s.encode();assert 2 not in ts;assert not any(a==b==16 for a,b in zip(ts,ts[1:]));r.update(tokens=ts,body_tokens=len(ts)-1,origin='new-acquisition; exact old page/root excluded; near test pending',category=('procedure'if re.search('するには|方法|手順|まず|次に|すると|ようにします|してください',s)else'reason'if re.search('ため|なぜ|理由|したがって|そのため|なので',s)else'daily'if re.search('料理|食事|食べ|衣服|買い物|旅行|ホテル|宿泊|電車|列車|趣味|遊び',s)else'general-explanation'),author_status='pre2022 community revision; human/bot provenance not exhaustively verified; not an LLM-generated teacher')
   try:ipaddress.ip_address(r['last_editor']);r['last_editor']='[public-history-IP-not-republished]'
   except (ValueError,TypeError):pass
   seen.add(c);rows.append(r)
write('POOL_AUDIT.json',dict(acquired_pages=dict(pages),parsed_body_BPE_tokens=dict(acquired),eligible_records=len(rows),eligible_targets=sum(r['body_tokens']for r in rows),eligible_by_source={s:sum(r['body_tokens']for r in rows if r['source']==s)for s in sorted({r['source']for r in rows})},held=dict(held),raw_archive_SHA=raw_shas,source_roots={s:len({r['family']for r in rows if r['source']==s})for s in sorted({r['source']for r in rows})},new_network_corpus_acquisition=True))
(P/'pool.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False)for x in rows)+'\n').encode(),mtime=0));print('POOL',len(rows),'tokens',sum(r['body_tokens']for r in rows),'sources',collections.Counter({s:sum(r['body_tokens']for r in rows if r['source']==s)for s in {r['source']for r in rows}}),'held',dict(held))
