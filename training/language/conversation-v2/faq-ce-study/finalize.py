import pathlib,json,re,hashlib,collections,sys
P=pathlib.Path(__file__).parent;a=json.loads((P/'PREPARED.json').read_text());held=[]
def reject(r):
 z=r['question']+r['response']
 if re.search('(?<!愛)がん|癌|被ばく|被曝|放射線|線量|甲状腺|健康影響',z):return 'Radiation/medical risk claims excluded after individual reading'
 if re.search('御覧|以下リンク|調整していきたい',z):return 'Missing link or unresolved proposal'
 if re.search('この法律|この制度|窓口|派遣期間|不合格となった|内定後',r['question']):return 'Question presupposes unnamed law/agency/process'
 if r['index']in[13015,740]:return 'Individually read insufficient fee/reuse scope'
 return None
parts={}
for k in ['train','dev']:
 parts[k]=[]
 for r in a[k]:
  reason=reject(r)
  if reason:held.append(dict(id=r['id'],partition=k,reason=reason));continue
  parts[k].append(dict(r,history=[dict(role='user',text=r['question'])],license='CC-BY-4.0 compatible PDL1.0 official prose; per-source exclusions apply',source_revision='a9fd35ae0f7d984cef7c054cfa6ae68bc7b5d354',role_contract='slot3 question / slot4 original FAQ answer, not speaker identity',original_answer_unchanged=True))
parts['train'].sort(key=lambda r:hashlib.sha256(('faq-onepass-order-v1|'+r['id']).encode()).hexdigest());order=[list(range(i,min(i+4,len(parts['train']))))for i in range(0,len(parts['train']),4)]
data=dict(parts=parts,batch_order=order,updates_per_arm=len(order),midpoint=(len(order)+1)//2,one_pass=True,ASDC_training_positions=0,ASDC_eval_only=True)
(P/'DATA.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
summary={k:dict(cases=len(z),body_tokens=sum(r['body_tokens']for r in z),input_tokens=sum(len(r['tokens'])-1 for r in z),response_EOS=len(z),families=len({r['split_family']for r in z}),sources=dict(collections.Counter(r['source']for r in z)),proxy_categories=dict(collections.Counter(r['category_proxy']for r in z)))for k,z in parts.items()}
(P/'DATA_AUDIT.json').write_text(json.dumps(dict(partitions=summary,final_holds=held,prior_holds=a['held'],near_links=a['near_links'],quality_original_sample_ids=a['quality_sample_ids'],quality_sample_remaining=[r['id']for r in parts['train']if r['id']in a['quality_sample_ids']],all_DEV_read=True,original_full_corpus_not_manually_approved=True,admission='deterministic whole-population gates plus fixed stratified reading, not individual manual approval of every TRAIN answer',revision_answer_date='HF revision2024-02-29; individual updated dates preserved when in answer, otherwise unknown; never assumed current2026',model_calls_before_freeze=0,MAFF_entire_source_held_out=True),ensure_ascii=False,indent=2)+'\n');print(summary,'updates',len(order))
