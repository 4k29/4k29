import collections,gzip,hashlib,importlib.util,json,pathlib,re
H=pathlib.Path(__file__).resolve().parent;V=H.parent
rank=lambda s:hashlib.sha256(('grounded-v1|'+s).encode()).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('own',V/'new_tokenizer.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);tok=json.loads((V/'data/tokenizer.json').read_text());enc=m.Encoder(tok);pieces=[bytes.fromhex(x)for x in tok['bytes']];blocked={c['source']['entity_family']for c in json.loads((V/'response-data/final/active-dev.json').read_text())['cases']};entities={};conflicts=set()
 for l in gzip.open('/dev/shm/grounded-source/train.jsonl.gz','rt'):
  r=json.loads(l)
  for t in r['data']['turns']:
   e=t.get('dialogue_state',{}).get('db_result',{}).get('active_entity')or{};name=e.get('name')
   if not name or name in blocked or'天気'in name:continue
   f={k:str(e[k])for k in ['name','parking','wifi','adultfee','childfee','area']if k in e};ident=json.dumps(f,ensure_ascii=False,sort_keys=True)
   if name in entities and entities[name]['facts']!=f:conflicts.add(name)
   entities.setdefault(name,{'facts':f,'source_dialogue':r['source_id'],'source_object_sha256':r['source_object_sha256'],'source_turn':t['turn_id'],'license':'CC-BY-SA-4.0'})
 rows=[]
 for name,e in sorted(entities.items()):
  if name in conflicts:continue
  f=e['facts'];split='DEV'if int(rank(name)[:8],16)%5==0 else'TRAIN';tasks=[]
  for slot,label in [('parking','駐車場'),('wifi','Wi-Fi')]:
   if f.get(slot)in['有り(無料)','有り(有料)','無し']:
    value=f[slot];text={'有り(無料)':label+'は無料で利用できます。','有り(有料)':label+'は有料です。','無し':label+'はありません。'}[value];tasks.append((slot,'資料にある'+label+'の利用条件を教えてください。'if split=='TRAIN'else'この記録では'+label+'を使えますか。料金も含めて答えてください。',text,[value],dict(f)))
  if all(k in f and re.fullmatch(r'\d+',f[k])for k in ['adultfee','childfee']):
   tasks.append(('fee','子供の入場料はいくらですか。'if split=='TRAIN'else'資料を見て、子供が入場する場合の金額を答えてください。','子供の入場料は'+f['childfee']+'円です。',[f['childfee']],dict(f)))
   for swapped in [False,True]:
    ff=dict(f)
    if swapped:ff['adultfee'],ff['childfee']=ff['childfee'],ff['adultfee']
    adult,child=int(ff['adultfee']),int(ff['childfee']);label='同じ'if adult==child else'大人'if adult<child else'子供';answer='両方の料金は同じです。'if label=='同じ'else label+'の料金が安いです。';tasks.append(('compare-swap'if swapped else'compare','仮定資料の大人料金と子供料金を比べ、安い方か同額かを答えてください。'if split=='TRAIN'else'この仮定の料金表で、大人と子供のどちらがお得ですか。同額ならそう答えてください。',answer,[label],ff))
  if all(f.get(k)in['有り(無料)','有り(有料)','無し']for k in ['parking','wifi']):
   yes=all(f[k]=='有り(無料)'for k in ['parking','wifi']);tasks.append(('condition','駐車場とWi-Fiが両方無料という条件を満たしますか。'if split=='TRAIN'else'駐車場もWi-Fiもお金がかからないことが希望です。資料の施設は該当しますか。','両方無料なので条件を満たします。'if yes else'両方無料ではないため条件を満たしません。',['満たします'if yes else'満たしません'],dict(f)))
  # Max 4 tasks/entity, non-repeating independent case IDs, entity facts are not multiplied as original text.
  for task,q,a,required,ff in sorted(tasks,key=lambda x:rank(name+'|'+x[0]))[:4]:
   context='、'.join({'name':'施設','parking':'駐車場','wifi':'Wi-Fi','adultfee':'大人料金','childfee':'子供料金','area':'地域'}[k]+':'+ff[k]for k in sorted(ff));header='仮定の料金資料（現実の料金とは限りません）'if task.startswith('compare')else'原典収集時点の資料（現在の情報とは限りません）';prompt=header+'\n'+context+'\n質問：'+q;pre=[1,3]+enc(prompt)+[2,4];ans=enc(a)+[2]
   if len(pre)>192 or len(pre+ans)>257 or len(ans)>64:continue
   assert b''.join(pieces[t]for t in enc(prompt)).decode()==prompt
   rows.append(dict(id=rank(name+'|'+task),entity=name,split=split,task=task,prompt=prompt,answer=a,required=required,prefix=pre,answer_ids=ans,sequence=pre+ans,answer_start=len(pre),provenance=e,counterfactual=task=='compare-swap',authorship='program-composed teacher; no human-answer or external LLM claim'))
 train=sorted([r for r in rows if r['split']=='TRAIN'],key=lambda r:rank(r['id']));dev=sorted([r for r in rows if r['split']=='DEV'],key=lambda r:rank(r['id']));assert len(train)>=1024
 (H/'data.json').write_text(json.dumps({'train':train,'dev':dev},ensure_ascii=False,separators=(',',':'))+'\n');(H/'DATA_AUDIT.json').write_text(json.dumps({'train_cases':len(train),'dev_cases':len(dev),'train_entities':len({r['entity']for r in train}),'dev_entities':len({r['entity']for r in dev}),'entity_overlap':len({r['entity']for r in train}&{r['entity']for r in dev}),'conflicting_entities_held':len(conflicts),'old23_entities_excluded':len(blocked),'program_teacher_not_human_written':True,'independent_human_evaluation':False,'max_cases_per_entity':4,'tasks':dict(collections.Counter(r['task']for r in train)),'source_unique_fact_utf8_bytes':sum(len(json.dumps(e['facts'],ensure_ascii=False).encode())for n,e in entities.items()if n not in conflicts),'source_license':'CC-BY-SA-4.0','raw_dialogues_not_published':True},ensure_ascii=False,indent=2)+'\n');print('train/dev',len(train),len(dev))
if __name__=='__main__':main()
