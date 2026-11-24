"""Explicit main-assistant original-text adjudication, not regex semantic inference."""
import json,pathlib,hashlib,collections,statistics
__import__('os').umask(0o077)
P=pathlib.Path(__file__).resolve().parent
raw=json.loads((P/'LOCAL_REVIEW_CARDS.json').read_text())
holds={3:'why-skydiving question and reply motivation insufficiently aligned; not repaired',8:'caffeine-effect discussion needs factual/health-context qualification',11:'historical programme-origin assertion in context not independently checked',15:'unverified physiological explanation about coffee after waking',17:'anonymization placeholder in history; kept unchanged and withheld from candidate input',19:'personal gastrointestinal-health statement',28:'finger-count joke/premise ambiguous; not treated as a factual explanation',38:'anonymization placeholder in history',56:'animal population-control procedural advice incomplete/unverified; no factual approval',63:'song recommendation does not identify a song; unit/new-release claim not verified',69:'rice/curry referent unclear; no sentence repair',70:'anonymization placeholder in history',76:'publication/serialization claim needs primary-source checking; natural writing is not factual certification',77:'personal persistent daytime-sleepiness discussion; health context',84:'family health/divination claim; unverifiable and personal',98:'concentration-benefit/marketing assertions not verified',105:'personal family conflict in history; excluded from this narrow candidate pack',120:'unmasked nickname in context; no silent anonymization',129:'reply does not answer whether practice occurs at home',145:'malformed proper name in history; all-CE would also learn it; no correction',152:'response does not clearly resolve viewing question',187:'anonymization placeholder in history'}
followup={2,14,20,37,39,41,44,46,47,49,51,54,64,72,74,75,80,87,95,100,102,112,126,139,165,173,182,191}
limited={48,59,61,79,83,101,154,157,160,176,181}
reason={0,4,5,6,7,10,12,13,18,22,23,24,26,27,29,30,31,50,89,96,142,146,147,161,170,175,185}
comparison={35,43,45,53,85,91,92}
procedural={25,107}
explanation={1,9,52,65,88,103,125,128,130,131,158,162,186}
advice={57,58,62,71,73}
contextual={16,21,60,82,90,119,133,136,140,150,159,164,166,172,177,179,188,189}
devholds={4:'multiple past and current residence regions; unnecessary quasi-identifying trajectory',9:'store-exclusivity/product claim not independently verified',12:'quiz/joke has no unique context-grounded answer',15:'child schooling/personal circumstances; withheld'}
devlimited={1}
devfollow={5,6,10,22,23}
rows=[]
for part in ['train','dev']:
 for i,r in enumerate(raw[part]):
  if part=='train':
   if i in holds:decision,kind,why='hold','unresolved',holds[i]
   elif i in limited:decision,kind,why='natural_limited','ack_or_low_specificity','Natural social response but insufficient new required information for this content-focused comparison; not erased from language modelling.'
   elif i in followup:decision,kind,why='conditional_candidate','clarifying_or_followup','Related question/condition restatement adds a concrete next conversational action; not a direct answer or verified constraint fulfilment.'
   else:
    kind='reason' if i in reason else 'choice_or_contrast' if i in comparison else 'procedure' if i in procedural else 'explanation' if i in explanation else 'advice' if i in advice else 'contextual_detail' if i in contextual else 'concrete_answer'
    decision,why='conditional_candidate','Complete visible history and reply are related and contain specific information/opinion. Human self-report remains human self-report, not assistant identity or independently established fact.'
  else:
   if i in devholds:decision,kind,why='hold','unresolved',devholds[i]
   elif i in devlimited:decision,kind,why='natural_limited','ack_or_low_specificity','Empathic short remark, not a content-required evaluation task.'
   elif i in devfollow:decision,kind,why='conditional_candidate','clarifying_or_followup','Concrete follow-up on visible topic; evaluation must allow alternatives rather than exact reference match.'
   else:decision,kind,why='conditional_candidate',('reason' if i in [0,2] else 'procedure' if i==3 else 'advice' if i==14 else 'concrete_answer'),'Human context/reply relation readable; self-attribute/opinion reference is not the only acceptable reply, so no factual gold or unique-answer claim.'
  rows.append(dict(partition=part,index=i,id=r['id'],document=r['document'],family=r['family'],retrieval_stratum=r['selection_stratum'],decision=decision,semantic_type=kind,reason=why,full_history_and_reply_read=True,formal_independent_human_review=False,original_role_retained=True,reply_body_tokens=len(r['response_ids'])-1,source_text_sha256=r['source_text_sha256'],prefix_sha256=hashlib.sha256(json.dumps(r['prefix_ids'],separators=(',',':')).encode()).hexdigest(),response_sha256=hashlib.sha256(r['response_text'].encode()).hexdigest(),source_facts_independently_verified=False))
(P/'REVIEW.json').write_text(json.dumps(dict(judge='main assistant only, non-blind',population_quality_certified=False,formal_TRAIN_admission=False,cases=rows),ensure_ascii=False,indent=2)+'\n')
for part in ['train','dev']:
 rr=[r for r in rows if r['partition']==part];print(part,dict(collections.Counter(r['decision']for r in rr)),dict(collections.Counter(r['semantic_type']for r in rr if r['decision']=='conditional_candidate')), 'response_tokens',sum(r['reply_body_tokens']for r in rr if r['decision']=='conditional_candidate'))
