"""Conservative exclusion before semantic reading. Does not certify surviving responses."""
import pathlib,json,re,collections
P=pathlib.Path(__file__).resolve().parent;rows=json.loads((P/'PRIVATE/REVIEW_CARDS.json').read_text());holds=[];survive=[]
if(P/'PRE_REVIEW_GATES.json').exists()and not(P/'PRE_REVIEW_GATES-v1.json').exists():(P/'PRE_REVIEW_GATES-v1.json').write_bytes((P/'PRE_REVIEW_GATES.json').read_bytes())
for i,r in enumerate(rows):
 reasons=[];before='\n'.join(z['text']for z in r['history']);allagent='\n'.join([z['text']for z in r['history']if z['role']=='agent']+[r['response']])
 if re.search('ございますが|ご用意でき|ご用意して|完備|当ホテル|当館|この宿|こちらのホテル|対応しており|利用できます|備えております|無料で提供|可能でございます|お部屋がございます',allagent):reasons.append('unsupported_specific_inventory_or_service_assertion')
 nums=lambda s:set(re.findall(r'\d+(?:[,.]\d+)*',s))
 if nums(r['response'])-nums(before):reasons.append('new_numbers_require_external_basis')
 if re.search('ヒルトン|JAL|ANA|じゃらん|楽天|糖尿|血圧|病気|治療|医師|痛風|手術|電話番号',before+r['response']):reasons.append('external_product_or_medical_claim_context')
 allagent_without_greeting=re.sub('ありがとうございます[。！？!?]*','',allagent)
 if re.search('ございます[。が]|あります[。が]|が[有あ]り|付いています|お楽しみいただけ|ご案内できます|別料金|朝夕食事なしですが|ホテルはいかが|旅館はいかが|宿はいかが|お部屋はいかが',allagent_without_greeting):reasons.append('existence_or_offer_claim_requires_missing_DB')
 if not re.search('希望|予算|人数|何名|何人|何泊|泊数|日付|いつ|どちら|どこ|何|お考え|具体|お聞かせ|教えて|お伺い|年齢|お子様|アレルギー|苦手|こだわり|それとも|夕食|朝食|お食事',r['response']):reasons.append('not_specific_information_request_or_grounded_restatement')
 prior=''
 for turn in r['history']:
  if turn['role']=='agent'and nums(turn['text'])-nums(prior):reasons.append('earlier_agent_numeric_claim_without_history')
  prior+=turn['text']+'\n'
 if r['history']and r['history'][0]['role']=='user'and re.match('^(いいですね|宜しくお願いします[。!！]*$|よろしくお願いします[。!！]*$|他に|そうですね[。!！]*$)',r['history'][0]['text']):reasons.append('orphaned_opening_context')
 if reasons:holds.append(dict(index=i,id=r['id'],reasons=reasons))
 else:survive.append(dict(index=i,**r))
(P/'PRE_REVIEW_GATES.json').write_text(json.dumps(dict(rules='Hold unsupported inventory/service assertions, numeric values absent from complete history, and external medical/product contexts. Survivors require semantic review; no proxy acceptance.',held=holds,survivor_indices=[r['index']for r in survive],source_contract='actual operator replies only; original text unchanged',optimizer_updates=0),indent=2)+'\n');(P/'PRIVATE/SURVIVORS.json').write_text(json.dumps(survive,ensure_ascii=False,indent=2));print('held',len(holds),'survivors',len(survive),collections.Counter(r['partition']for r in survive));print('bodytokens',sum(r['body_tokens']for r in survive if r['partition']=='train'))
