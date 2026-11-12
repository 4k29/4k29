"""Apply main-agent full-history reading; no programmatic proxy is a semantic pass."""
import pathlib,json,collections,hashlib,re,difflib,unicodedata
P=pathlib.Path(__file__).resolve().parent;rows=json.loads((P/'PRIVATE/REVIEW_CARDS.json').read_text());survivors=set(json.loads((P/'PRE_REVIEW_GATES.json').read_text())['survivor_indices'])
train={2,11,12,14,15,16,18,19,20,22,24,33,36,41,46,47,50,51,60,69,77,80,91,107,112,118,121,123,132,134,137,140,146,147,170,171,178,184,186,200,213,220,225,227,230,238,241,242,255,259,260,271,278,301,318,321,323,326,340,353,364,365,370,373,375,380,381,383}
dev={387,388,389,391,394,404,415,416,420,435,441,445,450,452,455,476}
held={27:'Missing referent for こちら; implies unprovided candidate lodging',30:'Earlier all-CE history contains unverified area lodging distribution',44:'Unprovided Niigata/food reputation offer',73:'Asserts available security-equipped lodging without source evidence',84:'Product/origin generalization not verified',85:'Invented rail absence and bed-reconfiguration availability',116:'Unprovided budget-to-meal availability assertion',125:'Unprovided lodging amenities offer',135:'Unprovided nearby attraction/family plan plus malformed text',143:'Bed-sharing permission requires age and property rules',155:'Vague restatement does not clarify a concrete condition',158:'Autumn foliage season not present in input',168:'Unverified soundproofing cost claim',169:'Unprovided convention-location lodging scarcity',174:'External local transport recommendation not verified for this grounded-only subset',199:'Unprovided specific room-view/meal plan offer',229:'Unprovided allergy menu-change availability',232:'Unprovided broad allergy-friendly inventory assertion',233:'Unintroduced course/application-list service promise',234:'Unprovided cuisine/allergy accommodation offer',239:'Earlier history contains blanket allergy safety assurance and new availability',244:'Unverified universal Kyoto culinary quality assertion',249:'Unprovided specialist-chef lodging candidate',253:'Promises room-service delivery not established in input',258:'Implicit hotel context and meal-delivery availability not sufficiently grounded',266:'Unprovided specific review/meal-price offer',273:'Asks cuisine choice again although user explicitly accepts all; weak condition use',282:'Unprovided buffet availability proposal',302:'Unprovided breakfast location choice availability',304:'Earlier all-CE history asserts in-room dining availability without evidence',313:'Malformed target お探いたします; source not repaired',314:'Unprovided child welcome plan',316:'Generic promise and request without useful specific content',320:'Unprovided child event/souvenir lodging plan',332:'Unverified blanket buffet price claim',341:'Unprovided sushi counter availability',357:'Unprovided portion-adjustment guarantee',371:'Unprovided outdoor barbecue lodging offer',385:'Changes the requested breakfast dimension without clearly using Japanese-food preference',386:'Unprovided per-room cottage price assumption',396:'Excessive repetition of the same internet-free condition',406:'Claims exactly two people were already specified although not in history',412:'References missing prior budget and candidate suite pricing',419:'Generic promise without concrete condition clarification',433:'Strengthens a preference into an unasked mandatory condition',442:'Malformed target お探いたします; not repaired',443:'Unprovided allergy food/air-purifier availability',456:'Malformed target ごさいます; not repaired',461:'Unprovided milk-water service availability',463:'Definite packed-meal service promise without source evidence',471:'Unprovided review/availability claim'}
assert (train|dev)<=survivors;admitted={k:[]for k in ['train','dev']};judgments=[]
for i in sorted(survivors):
 r=rows[i];ok=i in train|dev;reason='Full original history and operator response read: useful condition restatement, missing-information question or hypothetical search criterion; no asserted real inventory or DB outcome. Fictional operator scope only.'if ok else held[i]
 cats=[]
 if ok:
  cats=['clarification'];cats+=['immediate_context_reference']
  if len(r['history'])>=3:cats+=['past_turn_context']
  if re.search('お探し|お調べ|ご紹介|ご提案',r['response']):cats+=['prospective_search_or_proposal']
  if len([x for x in re.split('[。?？]',r['response'])if x.strip()])>=2:cats+=['multiple_sentences']
  admitted[r['partition']].append(dict(r,manual_index=i,semantic_review=reason,categories=cats,research_authorized=True,formal_model_adoption=False,attribution='Yuta Hayashibe, Megagon Labs, Accommodation Search Dialog Corpus (LREC2022/NLP2021), CC-BY-4.0',source_url='https://github.com/megagonlabs/asdc/blob/f37d6575c73602adcb8ae3687520726793baa672/'+r['source_file']))
 judgments.append(dict(index=i,id=r['id'],partition=r['partition'],status='research_candidate'if ok else'hold',reason=reason,categories=cats,body_tokens=r['body_tokens'],independent_human_review=False))
# Preserve official partition, exclude same family and exact/near response across partitions.
canon=lambda s:''.join(unicodedata.normalize('NFKC',s).split()).casefold();excluded=[];kept=[]
for r in admitted['train']:
 conflicts=[d['id']for d in admitted['dev']if r['family']==d['family']or canon(r['response'])==canon(d['response'])or difflib.SequenceMatcher(None,canon(r['response']),canon(d['response']),autojunk=False).ratio()>=.85]
 if conflicts:excluded.append(dict(id=r['id'],dev_ids=conflicts,reason='family or normalized response exact/near overlap'))
 else:kept.append(r)
# Known MAIN operator identities can be separated even though crowd worker IDs are unavailable.
# Keep operator1 MAIN DEV; operator2 MAIN TRAIN. Never move an official DEV row to TRAIN.
removed=[]
for part,allowed in [('train','operator_2'),('dev','operator_1')]:
 group=kept if part=='train'else admitted['dev'];allowed_rows=[]
 for r in group:
  if r['author_ids_available']and r['original_speaker']!=allowed:removed.append(dict(id=r['id'],reason='known MAIN operator held-out separation',partition=part));continue
  allowed_rows.append(r)
 admitted[part]=allowed_rows
excluded.extend(removed)
kept=admitted['train']
# Stable one-pass order and fixed batches; no source-position repetition.
admitted['train'].sort(key=lambda r:hashlib.sha256(('asdc-ce-onepass-v1|'+r['id']).encode()).hexdigest());batches=[list(range(i,min(i+4,len(kept))))for i in range(0,len(kept),4)]
for r in sum(admitted.values(),[]):
 assert r['tokens'][0]==1 and r['tokens'][r['response_body_start']-1]==4 and r['tokens'][-1]==2 and len(r['tokens'])<=257
for rs in admitted.values():assert len({r['family']for r in rs})==len(rs)
summary={s:dict(responses=len(rs),body_tokens=sum(r['body_tokens']for r in rs),input_tokens=sum(len(r['tokens'])-1 for r in rs),response_teachers=sum(r['body_tokens']+1 for r in rs),topics=dict(collections.Counter(r['topic']for r in rs)),known_original_speaker_names=sorted({u['original_name']for r in rs if r['author_ids_available']for u in r['history']}),worker_independence='Selected MAIN operator/customer IDs disjoint; crowd author IDs unavailable, so not globally author-independent TEST')for s,rs in admitted.items()}
data=dict(parts=admitted,batch_order=batches,updates_per_arm=len(batches),source='ASDC only; no ichikara descendants, no news/tweet content',scope='exploratory condition-clarification/operator-response CE comparison, not broad assistant-instruction learning',common_initial='PR108 MIX-579',one_pass=True,formal_adoption=False)
(P/'DATA.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n');(P/'REVIEW.json').write_text(json.dumps(dict(semantic_cases=judgments,automatic_gate_holds=len(rows)-len(survivors),all_survivors_full_history_read=True,source_texts_unchanged=True,reviewer='main assistant only, nonblind'),indent=2)+'\n');(P/'DATA_AUDIT.json').write_text(json.dumps(dict(parts=summary,overlap_exclusions=excluded,updates_per_arm=len(batches),one_pass=True,source_teacher_positions_repeated=False,source_raw_has_publisher_normalization=True,own_model_updates_before_freeze=0),ensure_ascii=False,indent=2)+'\n');print(summary);print('updates',len(batches),'overlap exclusions',excluded)
