import os
import pathlib,json,gzip,hashlib,re,sys,collections,zlib,unicodedata,statistics
C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'));V=pathlib.Path(__file__).resolve().parents[2];P=V/'novel-continuous-study';assert not(P/'PLAN.json').exists();sys.path.insert(0,str(V));from new_tokenizer import Encoder
enc=Encoder(json.loads((V/'data/tokenizer.json').read_text()));pieces=[bytes.fromhex(x)for x in json.loads((V/'data/tokenizer.json').read_text())['bytes']];canon=lambda s:''.join(unicodedata.normalize('NFKC',s).split());sha=lambda b:hashlib.sha256(b).hexdigest();write=lambda n,v:(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
wiki=[json.loads(x)for x in gzip.decompress((P/'pool.jsonl.gz').read_bytes()).splitlines()];gv=json.loads((C/'gv-parsed.json').read_text());faq=json.loads((V/'faq-ce-verified-study/DATA.json').read_text());dev=json.loads((P/'NEW_PROSE_DEV.json').read_text())['cases']+json.loads((V/'foundation-absorption-study/PROSE_DEV.json').read_text())['cases'];refs=[b''.join(pieces[t]for t in w['tokens']if t>=6).decode('utf8',errors='ignore')for w in json.loads(gzip.decompress((V/'mixed-retention-study/DEV_BODY_NLL.json.gz').read_bytes()))]+[r[k]for r in faq['parts']['train']+faq['parts']['dev']for k in['question','response']]+[r['text']for r in dev];smallrefs=[canon(r)for r in refs if len(canon(r))>=8];old=json.loads(gzip.decompress((C/'PRIOR_TEXTS.json.gz').read_bytes()));reference=[('prior:'+r['id'],r['text'])for r in old]+[('protected:'+str(i),r)for i,r in enumerate(refs)]
def sig(s):
 s=canon(s);return {zlib.crc32(s[i:i+13].encode())for i in range(max(0,len(s)-12))}
index=collections.defaultdict(list);sets=[];names=[]
for name,text in reference:
 ss=sig(text)
 if len(ss)<64:continue
 n=len(sets);sets.append(ss);names.append(name)
 for k in ss:index[k].append(n)
held=collections.Counter();near=[];rows=[];seen=set();quality=json.loads((P/'DEVELOPMENT_QUALITY_REVIEW.json').read_text())
# The order is fixed before predictions. No source filling after model outcomes.
allrows=wiki+gv;allrows.sort(key=lambda r:sha(('source-quality-pool-v1|'+r['id']).encode()))
for r in allrows:
 if r.get('family')in quality['hold_families']or r.get('pageid')in quality['hold_pageids']or re.search(quality['additional_regex'],r['text']):held['development_quality_hold']+=1;continue
 if re.match(r'^(?:[）)、。]|は流体|このような|そのため|このため|それら|これら|前項|前述)',r['text']):held['missing_initial_context']+=1;continue
 c=canon(r['text'])
 if c in seen:held['exact_internal']+=1;continue
 if any(x in c or c in x for x in smallrefs):held['protected_exact_substring']+=1;continue
 if re.search(r'お前|馬鹿|バカ|死ね|キチガイ|頭が悪|劣等|発達障害|精神病|自殺|万引|死刑|性交|性感染|がん治療|ダイエット|診断|電話番号|メールアドレス',r['text']):held['sensitive']+=1;continue
 ts=[1]+enc(r['text'])+([2]if r['EOS']else[])
 if not 80<=len(ts)<=1800:held['BPE_length']+=1;continue
 ss=sig(r['text']);hits=collections.Counter(j for k in ss for j in index.get(k,[]));match=None
 if len(ss)>=64:
  for j,n in hits.most_common():
   if n<4:break
   if n/min(len(ss),len(sets[j]))>=.85:match=names[j];break
 if match is not None:near.append(dict(id=r['id'],matched=match,action='held'));held['near_prior_protected_or_internal']+=1;continue
 assert b''.join(pieces[t]for t in ts if t>=6)==r['text'].encode();assert not any(a==b==16 for a,b in zip(ts,ts[1:]));assert all(t>=6 for t in (ts[1:-1]if r['EOS']else ts[1:]))
 r.update(tokens=ts,body_tokens=sum(t>=6 and t!=16 for t in ts),all_targets=len(ts)-1,origin='newly acquired/reacquired previously untrained prose; no known prior page/root, canonical or near match; complete semantic novelty not guaranteed',category=r.get('category')or('procedure'if re.search('するには|方法|手順|まず|次に|すると|ようにします|してください',r['text'])else'reason'if re.search('ため|なぜ|理由|したがって|そのため|なので',r['text'])else'daily'if re.search('料理|食事|食べ|衣服|買い物|旅行|ホテル|宿泊|電車|列車|趣味|遊び',r['text'])else'general-explanation'))
 rows.append(r);seen.add(c)
 if len(ss)>=64:
  n=len(sets);sets.append(ss);names.append('new:'+r['id'])
  for k in ss:index[k].append(n)
(P/'new-pool-reviewed-by-machine.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(r,ensure_ascii=False)for r in rows)+'\n').encode(),mtime=0));write('NEAR_AUDIT.json',dict(reference_records=len(reference),candidate_records=len(allrows),remaining_records=len(rows),remaining_targets=sum(r['all_targets']for r in rows),by_source={s:sum(r['all_targets']for r in rows if r['source']==s)for s in sorted({r['source']for r in rows})},held=dict(held),near_holds=near,method='13-character crc32 shingle; >=64 signatures,>=4 shared candidates,85%shorter containment. Combined exact substring protection. Not exhaustive semantic/family independence proof.',optimizer_calls=0,model_forwards=0));print('near eligible',len(rows),sum(r['all_targets']for r in rows),collections.Counter({s:sum(r['all_targets']for r in rows if r['source']==s)for s in {r['source']for r in rows}}))
