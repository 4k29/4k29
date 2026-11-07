"""Pre-inference deterministic selection and matched unrelated source histories."""
import pathlib,json,hashlib,collections,re,datetime
from candidate_source import build_inventory,P as BASE
D=pathlib.Path(__file__).resolve().parent
SEED='paragraph-context-use-v1|20261107'
def h(s):return hashlib.sha256(s.encode()).hexdigest()
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(n,x):(D/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def score(head,text,topics):
 s={k:sum(min(len(w),6)*(2*head.count(w)+text.count(w))for w in ws)for k,ws in topics.items()}
 k=max(s,key=s.get);return k if s[k]>0 else'unknown',s

def main():
 assert not(D/'FREEZE.json').exists(),'Frozen input pairs must not be rebuilt'
 inv=build_inventory();topics=inv['topics'];pieces=[bytes.fromhex(s)for s in json.loads((BASE.parent/'data/tokenizer.json').read_text())['bytes']]
 candidates=[x for x in inv['candidates']if not x['special_pattern']and any(w in x['history_text']for w in topics[x['topic']])]
 years=sorted({r['year']for r in candidates});assert len(years)==8
 counts=collections.Counter();option_cache={}
 manual=json.loads((D/'MANUAL_DONOR_CONSTRAINTS.json').read_text())if(D/'MANUAL_DONOR_CONSTRAINTS.json').exists()else{}
 rejected={r['pair_key']for r in json.loads((D/'PREINFERENCE_REJECTIONS.json').read_text())}if(D/'PREINFERENCE_REJECTIONS.json').exists()else set()
 def donor_options(c):
  if c['key']in option_cache:return option_cache[c['key']]
  out=[];L=c['length']
  for u in inv['donors']:
   if c['key']+'|'+u['key']in rejected:continue
   if u['document_family']==c['document_family']or u['heading_family']==c['heading_family']or u['length']<L:continue
   ids=u['history_tokens'][-L:]
   if any(t<6 for t in ids):continue
   raw=b''.join(pieces[t]for t in ids)
   try:text=raw.decode('utf8')
   except UnicodeDecodeError:continue
   if '。'not in text or len(re.findall(r'[一-龯ぁ-んァ-ヶ]',text))<30:continue
   tp,sc=score(u['heading'],text,topics)
   rule=manual.get(c['key'],{})
   if rule.get('allowed_donor_topics')and tp not in rule['allowed_donor_topics']:continue
   if any(w in u['heading']+text for w in rule.get('forbid_words',[])):continue
   if tp=='chemicals_pollution'and not any(w in text for w in ['化学物質','大気','公害','騒音','振動','アスベスト','土壌']):continue
   if tp=='unknown'or tp==c['topic']or sc[c['topic']]or c['topic_scores'][tp]:continue
   if not any(w in text for w in topics[tp]):continue
   out.append(dict(**{k:v for k,v in u.items()if k not in ['history_tokens','history_text','length','topic','topic_scores']},history_tokens=ids,history_text=text,length=L,topic=tp,topic_scores=sc,uncropped_length=u['length'],left_tokens_removed=u['length']-L,retained_source_start=u['ref']['start']+u['length']-L))
  out.sort(key=lambda u:(u['year']!=c['year'],h(SEED+'|donor|'+c['key']+'|'+u['key'])))
  option_cache[c['key']]=out;return out
 slots=[]
 for group in ['mata','other']:
  ys=sorted(years,key=lambda y:(sum(r['group']==group and r['year']==y for r in candidates),y))
  for _ in range(2):slots.extend((group,y)for y in ys)
 chosen=[];usedpages=set();usedheads=set();topicN=collections.Counter();goldN=collections.Counter();kindN=collections.Counter();quota={'content_or_other':8,'demonstrative':4,'connector':4}
 nodes=0
 def select(i):
  nonlocal nodes
  nodes+=1
  assert nodes<200000,'Selection search resource bound; report shortage, do not relax'
  if i==len(slots):return True
  group,year=slots[i]
  opts=[r for r in candidates if r['group']==group and r['year']==year]
  opts.sort(key=lambda r:((kindN[r['gold_kind']]/quota[r['gold_kind']]if group=='other'and r['gold_kind']in quota else 0),topicN[r['topic']],h(SEED+'|target|'+r['key'])))
  for c in opts:
   if c['document_family']in usedpages or c['heading_family']in usedheads or topicN[c['topic']]>=8:continue
   if group=='other'and(c['gold_kind']not in quota or kindN[c['gold_kind']]>=quota[c['gold_kind']]or goldN[c['gold']]>=2):continue
   if not donor_options(c):counts['target_attempts_without_donor']+=1;continue
   chosen.append(c);usedpages.add(c['document_family']);usedheads.add(c['heading_family']);topicN[c['topic']]+=1
   if group=='other':goldN[c['gold']]+=1;kindN[c['gold_kind']]+=1
   if select(i+1):return True
   chosen.pop();usedpages.remove(c['document_family']);usedheads.remove(c['heading_family']);topicN[c['topic']]-=1
   if group=='other':goldN[c['gold']]-=1;kindN[c['gold_kind']]-=1
  return False
 assert select(0),'Not enough cases under fixed constraints; no model run'
 targets=sorted(chosen,key=lambda c:(c['group']!='mata',c['year'],h(SEED+'|final|'+c['key'])))
 targetpages={c['document_family']for c in targets};targetheads={c['heading_family']for c in targets}
 options={c['key']:[u for u in donor_options(c)if u['document_family']not in targetpages and u['heading_family']not in targetheads]for c in targets}
 order=sorted(targets,key=lambda c:(len(options[c['key']]),h(SEED+'|match|'+c['key'])))
 assigned={};upages=set();uheads=set();matchnodes=0
 def match(i):
  nonlocal matchnodes
  matchnodes+=1;assert matchnodes<200000
  if i==len(order):return True
  c=order[i]
  for u in options[c['key']]:
   if u['document_family']in upages or u['heading_family']in uheads:continue
   assigned[c['key']]=u;upages.add(u['document_family']);uheads.add(u['heading_family'])
   if match(i+1):return True
   del assigned[c['key']];upages.remove(u['document_family']);uheads.remove(u['heading_family'])
  return False
 assert match(0),'Unrelated matching shortage; retain proposals and report, no forced fill'
 pairs=[]
 for i,c in enumerate(targets):
  u=assigned[c['key']];assert c['length']==u['length']and c['history_tokens'][-2:]==u['history_tokens'][-2:]==[16,16]
  assert not any(t<6 for t in c['history_tokens']+u['history_tokens'])
  pairs.append(dict(index=i,group=c['group'],gold=c['gold'],gold_piece=c['gold_text'],gold_kind=c['gold_kind'],correct=c,unrelated=u,positions=list(range(c['length'])),same_original_next_token=c['gold']==u['gold'],teacher_tail=c['tail_tokens']))
 reps=[];yearN=collections.Counter()
 for group in ['mata','other']:
  seen=set()
  for r in sorted((r for r in pairs if r['group']==group),key=lambda r:h(SEED+'|aux|'+r['correct']['key'])):
   if r['correct']['year']in seen or yearN[r['correct']['year']]>=2:continue
   reps.append(r['index']);seen.add(r['correct']['year']);yearN[r['correct']['year']]+=1
   if len(seen)==4:break
 assert len(reps)==8
 selection=dict(seed=SEED,raw_candidate_counts=inv['counts'],extra_eligible_no_BOS_and_topic_in_history=len(candidates),eligible_by_year_group=inv['eligible_by_year_group'],counts=dict(counts),selection_search_nodes=nodes,matching_search_nodes=matchnodes,
  selected_group_counts=dict(collections.Counter(r['group']for r in pairs)),selected_year_counts=dict(collections.Counter(r['correct']['year']for r in pairs)),nonmata_gold_ids=dict(goldN),nonmata_kinds=dict(kindN),selected_topic_counts=dict(topicN),
  selected_pages=len(targetpages),donor_pages=len(upages),combined_pages=len(targetpages|upages),combined_heading_families=len(targetheads|uheads),
  exact_source_family='All share env-whitepaper-series. Distinct document_family here means source HTML page, NOT independent authors/source providers.',
  pairs_same_year=sum(r['correct']['year']==r['unrelated']['year']for r in pairs),donor_crop_counts=dict(collections.Counter(str(r['unrelated']['left_tokens_removed'])for r in pairs)),
  supplemental_representatives=reps,old32_events_excluded=True,old8_target_pages_excluded=True,
  selected=[dict(index=r['index'],group=r['group'],correct={k:v for k,v in r['correct'].items()if k not in ['history_tokens','history_text']},unrelated={k:v for k,v in r['unrelated'].items()if k not in ['history_tokens','history_text']})for r in pairs])
 protocol=dict(version=1,seed=SEED,topic_keyword_dictionary=topics,optimizer_updates=0,model='Only own PR106 B-579',checkpoint_sha256='3cebff9801302bd9969601e539adccaca7e0ea83943cc96bf2dc0b35f0906b9c',
  criteria=dict(history_min=64,history_max=248,BOS_or_other_special_tokens='Exclude all in C/U; no artificial BOS insertion',UTF8='Require exact UTF8 history and8-token tail recovery; never retokenize/repair',readability='At least one。and30 Japanese characters in retained histories',year_group='Exactly2 cases per8 years per group, if constraints can be met; otherwise stop without inference',page='32 distinct C pages and32 disjoint U pages',heading='64 distinct NFKC/number-prefix-normalized heading strings, not semantic-family independence',topic='Fixed keyword proxy; different primary topics, no reciprocal specific-keyword overlap; human full-history review required before freeze',nonmata='8 content/other,4 demonstrative,4 other connector; max2 per gold BPE ID',donor='Prefer same year; if unavailable choose other year and record. Left crop original token prefix to exact C length; require UTF8, readability and no specials.'),
  decoder='Default positions0..L-1, batch1/no padding, eval/dropout off, full3997-vocab softmax; no LF/special exclusion or penalties',
  principal='Delta=logP(g|C)-logP(g|U), strict-positive count; not semantic success. Report overall balanced sample plus each16-case group; not population-representative.',
  delta_bins=['<-1','[-1,-.1)','[-.1,0]','(0,.1]','(.1,1]','>1'],near_zero_reporting_threshold_nats=.01,no_independent_sample_p_values=True,
  primary_condition_count=64,logits_reuse='Reuse exact B checkpoint+input token tuple from saved B archive; no reuse from other checkpoints.',
  auxiliary=dict(representatives=reps,teacher_tokens=8,additional_forward_max=16,primary_first=True,limits='Same original C tail given to both histories; prefix+7<=255; not free generation or knowledge-of-word segmentation.'),
  freeze='Write FREEZE only after semantic pair review; runner checks all source/code/input hashes.',
  source_sha256={str(p.relative_to(BASE.parents[3])):sha(p)for p in [BASE/'corpus.jsonl.gz',BASE/'schedule.json.gz',BASE.parent/'data/tokenizer.json',BASE/'NEWLINE_COLLAPSE_DIAGNOSIS.json',BASE/'newline-followup/EIGHT_CASE_AUDIT.json']})
 write('PROTOCOL.json',protocol);write('SELECTION.json',selection);write('INPUT_PAIRS.json',pairs)
 cards=[]
 for r in pairs:
  cards.append(f"CASE {r['index']} {r['group']} gold={r['gold_piece']} L={len(r['positions'])} AUX={r['index']in reps}\nC {r['correct']['year']} {r['correct']['heading']} [{r['correct']['topic']}]\n{r['correct']['history_text']}\nU {r['unrelated']['year']} {r['unrelated']['heading']} [{r['unrelated']['topic']}] crop={r['unrelated']['left_tokens_removed']}\n{r['unrelated']['history_text']}\n")
 (D/'REVIEW_CARDS.txt').write_text('\n'.join(cards))
 print(json.dumps({k:selection[k]for k in ['selected_group_counts','selected_year_counts','nonmata_gold_ids','nonmata_kinds','selected_topic_counts','selected_pages','donor_pages','combined_pages','combined_heading_families','pairs_same_year','supplemental_representatives']},ensure_ascii=False))
if __name__=='__main__':main()
