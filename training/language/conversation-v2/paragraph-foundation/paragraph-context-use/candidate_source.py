import pathlib,json,gzip,hashlib,collections,re,unicodedata
P=pathlib.Path(__file__).resolve().parent.parent
def build_inventory():
 plan=json.loads((P/'PLAN.json').read_text())
 for f in [P/'corpus.jsonl.gz',P/'schedule.json.gz',P.parent/'data/tokenizer.json']:
  assert hashlib.sha256(f.read_bytes()).hexdigest()==plan['input_sha256'][str(f.relative_to(P.parents[3]))]
 tok=json.loads((P.parent/'data/tokenizer.json').read_text());pieces=[bytes.fromhex(x)for x in tok['bytes']]
 schedule=json.load(gzip.open(P/'schedule.json.gz','rt'));refs=collections.defaultdict(list)
 for b,bs in enumerate(schedule['arms']['B']):
  for ri,r in enumerate(bs):refs[r['record']].append((b,ri,r))
 corpus={i:json.loads(s)for i,s in enumerate(gzip.open(P/'corpus.jsonl.gz','rt'))if i in refs}
 audit=json.loads((P/'newline-followup/EIGHT_CASE_AUDIT.json').read_text());old8={(x['source_id'],x['source_offset'])for x in audit['cases']};oldpages={x['source_id'].split(':')[1]for x in audit['cases']}
 old32={(x['source_id'],x['source_offset'])for x in json.loads((P/'NEWLINE_COLLAPSE_DIAGNOSIS.json').read_text())['models']['B-579']['true_TRAIN_two_newline_events']}
 TOPICS={
 'climate_energy':['温暖','温室','炭素','エネルギー','気候','CO2','再生可能','排出量'],
 'waste_recycling':['廃棄物','リサイクル','循環','再資源','ごみ'],
 'biodiversity':['生物多様性','生態系','野生','自然公園','外来','絶滅','里地','里山','国立公園','国定公園','動植物','鳥類','生息'],
 'water_marine':['水質','海洋','海域','河川','湖沼','地下水','水環境','赤潮'],
 'chemicals_pollution':['化学物質','大気','公害','騒音','振動','アスベスト','環境リスク','土壌'],
 'society_economy':['環境教育','環境学習','環境産業','環境配慮','金融','消費','地域づくり','人口','ESG','環境経済','教育','学習','教材'],
 'disaster_radiation':['東日本','震災','放射','除染','福島']}
 def topic(h,t):
  s={k:sum(min(len(w),6)*(2*h.count(w)+t.count(w))for w in ws)for k,ws in TOPICS.items()}
  k=max(s,key=s.get);return k if s[k]>0 else'unknown',s
 candidates=[];counts=collections.Counter();donors=[]
 for idx,row in corpus.items():
  for bi,ri,ref in refs[idx]:
   ts=row['tokens'][ref['start']:ref['start']+ref['length']]
   for j in range(2,len(ts)):
    if ts[j-2:j]!=[16,16]or ts[j]<6 or ts[j]==16:continue
    counts['visible_LF2_body_teacher']+=1
    pos=ref['start']+j;ids=ts[:j];raw=b''.join(pieces[t]for t in ids)
    try:text=raw.decode('utf8')
    except UnicodeDecodeError:counts['invalid_UTF8_history']+=1;continue
    tp,scores=topic(row['heading'],text)
    tail=row['tokens'][pos:pos+8];tail_raw=b''.join(pieces[t]for t in tail)
    rec=dict(key=row['id']+'@'+str(pos),source_id=row['id'],document_family=row['document_family'],heading=row['heading'],heading_family=re.sub(r'^\d+\s+','',re.sub(r'^[（(][^）)]+[）)]\s*','',unicodedata.normalize('NFKC',row['heading']))),year=row['publication_year'],source_url=row['source_url'],source_sha256=row['source_sha256'],text_sha256=row['text_sha256'],record=idx,ref=ref,batch_index=bi,row_index=ri,source_position=pos,teacher_logit_position=j-1,history_tokens=ids,history_text=text,length=len(ids),special_pattern=[(i,t)for i,t in enumerate(ids)if t<6],topic=tp,topic_scores=scores,gold=ts[j],gold_text=pieces[ts[j]].decode('utf8',errors='backslashreplace'),tail_tokens=tail)
    if (row['id'],pos)in old32:counts['previous32_event']+=1;continue
    donors.append(rec)
    if row['document_family']in oldpages:counts['prior8_page']+=1;continue
    if not 64<=len(ids)<=248:counts['length_outside_64_248']+=1;continue
    if '。'not in text or len(re.findall(r'[一-龯ぁ-んァ-ヶ]',text))<30:counts['too_little_readable_prose']+=1;continue
    if tp=='unknown':counts['topic_unknown']+=1;continue
    if len(tail)!=8 or any(t<6 for t in tail):counts['insufficient8_body_tail']+=1;continue
    try:tail_raw.decode('utf8')
    except UnicodeDecodeError:counts['tail_UTF8_cut']+=1;continue
    tail_text=b''.join(pieces[t]for t in row['tokens'][pos:pos+25]).decode('utf8',errors='replace')
    rec['group']='mata'if ts[j]==3749 else'other'
    rec['gold_kind']='demonstrative'if tail_text.startswith(('この','これ','その','それ','こうした','こういった'))else'connector'if tail_text.startswith(('さらに','一方','しかし','なお','そして','また'))else'numeric'if re.match(r'[0-9０-９]',tail_text)else'content_or_other'
    candidates.append(rec)
 counts['eligible']=len(candidates)
 result=dict(counts=dict(counts),eligible_by_year_group={str(y):{g:sum(r['year']==y and r['group']==g for r in candidates)for g in ['mata','other']}for y in sorted({r['year']for r in candidates})},by_BOS=dict(collections.Counter((r['group']+':'+str(bool(r['special_pattern'])))for r in candidates)),candidates=candidates,donors=donors,topics=TOPICS,old8=sorted(old8),old32=sorted(old32))
 return result
