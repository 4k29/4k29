"""Existing corpus broad search; fixed retrieval strata, never automatic semantic approval."""
import pathlib,json,hashlib,re,importlib.util,os,collections
P=pathlib.Path(__file__).resolve().parent;V=pathlib.Path(os.environ.get('CE_V2_ROOT','/workspace/4k29/training/language/conversation-v2'));O=pathlib.Path(os.environ.get('CE_PRIOR_ROOT',str(V/'response-ce-study')))
def main():
 cfg=json.loads((P/'PROTOCOL.json').read_text());old=json.loads((O/'SELECTION_METADATA.json').read_text());excluded={r['document']for r in old['selected']};excluded.update(r['document']for r in json.loads((O/'SUPPLEMENT_SELECTION.json').read_text())['selected']);spec=importlib.util.spec_from_file_location('own',V/'new_tokenizer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);tok=json.loads((V/'data/tokenizer.json').read_text());enc=m.Encoder(tok);pieces=[bytes.fromhex(t)for t in tok['bytes']];sensitive=re.compile(json.loads((V/'sns-data/pipeline/publication-policy.json').read_text())['sensitive_topic_regex']);out={};receipt={}
 for part in ['train','dev']:
  pool=[];counts=collections.Counter()
  for line in (V/'data'/f'{part}.docs.jsonl').open():
   d=json.loads(line);us=d['utterances'];counts['documents_searched']+=1
   if d['id']in excluded:counts['previously_read_docs_excluded']+=1;continue
   text='\n'.join(u['text']for u in us)
   if sensitive.search(text)or re.search(r'https?://|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',text):counts['privacy_topic_hold_docs']+=1;continue
   full=[1]
   for j,u in enumerate(us):
    ids=enc(u['text']);assert b''.join(pieces[t]for t in ids)==u['text'].encode();start=len(full)+1;full.extend([u['localRoleToken']]+ids+[2])
    if j<1:continue
    counts['adjacent_positions_searched']+=1
    if len(full)>257:counts['complete_history_over_context']+=1;continue
    if not 24<=len(ids)<=96:continue
    a=us[j-1]['text'];b=u['text'];question=bool(re.search('[?？]|教えて|どうすれば|どうしたら',a));tags=[]
    if question and re.search('なぜ(?!か)|どうして(?!も|ます)|理由',a):tags.append('reason')
    if question and re.search('どちら(?!に|へ|です|の地域|の山)|どっち|比較|比べ',a):tags.append('comparison')
    if question and re.search('なら|場合|だったら|とき|条件|以内|以上|以下|避け',a):tags.append('condition')
    if question and re.search('どうやって|方法|手順|やり方|コツ|どうすれば|どうしたら',a):tags.append('procedure')
    if question and j>=4 and re.search('それ|そちら|その|さっき|先ほど|前に|とき|理由',a):tags.append('context_reference')
    if question and len(re.findall('[。！？!?]',b))>=2:tags.append('multi_sentence')
    if tags:pool.append(dict(id=d['id']+':'+str(j),document=d['id'],family=d['normalizedDocumentFamily'],speakers=d['speakers'],source='RealPersona',partition=part,ordinal=j,tokens=full[:],response_body_start=start,history=[z['text']for z in us[:j]],response=b,tags=tags,source_sha256=d['sourceSha256'],source_text_sha256=d['sourceTextSha256'],source_url=d['sourceUrl'],license=d['license'],attribution=d['attribution']))
  selected=[];seen=set();quotas=cfg['selection']['TRAIN_quota'if part=='train'else'DEV_quota'];actual={}
  for tag,quota in quotas.items():
   n=0
   for r in sorted((r for r in pool if tag in r['tags']),key=lambda r:hashlib.sha256((cfg['seed']+'|'+part+'|'+tag+'|'+r['id']).encode()).hexdigest()):
    if r['family']in seen:continue
    selected.append(dict(r,stratum=tag));seen.add(r['family']);n+=1
    if n==quota:break
   actual[tag]=n
  out[part]=selected;receipt[part]=dict(counts=counts,pool=len(pool),pool_tags=collections.Counter(t for r in pool for t in r['tags']),selected=actual,source_SHA256=hashlib.sha256((V/'data'/f'{part}.docs.jsonl').read_bytes()).hexdigest())
 (P/'PRIVATE_CARDS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');(P/'SEARCH.json').write_text(json.dumps(dict(receipt=receipt,selection=[dict(partition=k,index=i,id=r['id'],document=r['document'],family=r['family'],stratum=r['stratum'],input_sha256=hashlib.sha256(json.dumps(r['tokens'],separators=(',',':')).encode()).hexdigest())for k,rs in out.items()for i,r in enumerate(rs)],predictions_seen=False,optimizer_calls=0),ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
