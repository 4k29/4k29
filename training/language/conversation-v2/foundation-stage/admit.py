"""Research-only admission after fixed sample reading, before model outputs."""
import collections,gzip,hashlib,json,pathlib,re
H=pathlib.Path(__file__).resolve().parent
FAMILY_HOLD={'学習方法','独学ガイド','高校受験ガイド','将棋','中学校社会 地理'}
RISK=re.compile(r'&[A-Za-z#0-9]+;|この章で紹介|最大限に活用|以下に.{0,30}示|以下.{0,20}解説|本業はは|英会陰|、、|,、')
TRAVEL=re.compile(r'運転|免許|ビザ|査証|労働許可|救助|通報|登山|料金|乗車券|旅券|パスポート|制裁|ガイド.{0,20}同行|政府|議会|首相|国王|領有|奴隷|戦争|チベット|北朝鮮|時間半|NT\$')
def main():
 sample=json.loads((H/'quality-sample.json').read_text());holds={7:'句読点の重複',10:'助詞/受身の不自然さ',12:'欠けた図表への参照',19:'根拠不明の法的断定',20:'争点のある領土を一面的に断定',22:'章参照の定型的結語',23:'推薦図書への根拠不明の断定',25:'箇条書き断片',28:'棋譜主体',29:'英会陰という誤記',31:'学説史の過度な単純化と断定',32:'入試/教材への未検証の一般化',34:'活用の不自然さ',35:'重複語と部活動の未検証情報',40:'経路/所要時間の疑義',41:'HTML実体参照と経路の疑義',44:'直訳調と政治説明の不自然さ',45:'四川語源の疑義と重複読点',46:'発見史/条約への単純化',47:'許可制度の断定と文末不自然',48:'時点依存の強い旅行/政治的行動助言',49:'運転習慣の一括断定',50:'歴史的生活の推測と直訳調',51:'山岳装備助言の信頼性',52:'施設一覧断片'}
 reviewed=[dict(index=i,id=r['id'],decision='hold'if i in holds else'conditional_research_quality',reason=holds.get(i,'現代日本語の意味を追える原文。原典の全事実/全執筆者は未検証。基盤用途でAI自身の経験にはしない。'),full_text_read=True)for i,r in enumerate(sample)]
 (H/'QUALITY_REVIEW.json').write_text(json.dumps(dict(reviewer='main assistant only, unblinded, not independent native-human evaluation',all63_full_texts_read=True,rows=reviewed),ensure_ascii=False,indent=2)+'\n')
 held_ids={r['id']for i,r in enumerate(sample)if i in holds};counts=collections.Counter();rows=[]
 for l in gzip.open(H/'candidates.jsonl.gz','rt'):
  r=json.loads(l);t=r['text'];reason=None
  if r['source']=='jawikibooks'and r['family'].split('|',1)[-1]in FAMILY_HOLD:reason='family_quality_risk_found_in_fixed_sample'
  elif r['id']in held_ids:reason='manually_held_unit'
  elif RISK.search(t):reason='markup_typos_or_missing_reference'
  elif sum(c in '▲△'for c in t)>=4 or sum(' - 'in s for s in t.splitlines())>=2:reason='list_or_board_not_prose'
  elif r['source']=='jawikivoyage'and TRAVEL.search(t):reason='time_critical_travel_legal_or_governance_advice'
  if reason:counts[reason]+=1;continue
  r['admission']='bounded_exploratory_foundation_only';r['human_only_proven']=False;rows.append(r)
 with (H/'admitted.jsonl.gz').open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:
   for r in rows:z.write((json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 by=collections.defaultdict(lambda:collections.Counter())
 for r in rows:
  c=by[r['split']];c['units']+=1;c['body_tokens']+=r['body_tokens'];c['characters']+=len(r['text']);c['true_processed_page_start']+=r['true_processed_page_start'];c['true_processed_page_end']+=r['true_processed_page_end']
 train=[r for r in rows if r['split']=='train'];dev=[r for r in rows if r['split']=='dev']
 for key in ['family','component']:
  assert not {r[key]for r in train}&{r[key]for r in dev}
 canon=lambda s:re.sub(r'\s+','',s)
 assert not {canon(r['text'])for r in train}&{canon(r['text'])for r in dev}
 report=dict(status='GO bounded research only; no formal model/data release approval',license_source_specific=['CC-BY-SA-3.0 JaQuAD','CC-BY-SA-4.0 Wikis'],whole_corpus_still_not_admitted=True,quality_sample63_reviewed=len(sample),held_rules_before_model_outputs=True,removed_units_by_reason=dict(counts),splits={k:dict(v)for k,v in by.items()},independent_body_tokens_are_not_repeated_targets=True,author_full_history_unknown=True,known_last_editor_disjoint=True,jaquad_author_ids_unknown=True,geographic_topic_and_semantic_near_independence_not_proven=True,human_or_AI_origin_risk='Dataset publisher human-QA provenance; public collaborative text with revision/attribution. Human-only not certified; bot/latest-name and explicit generator markers filtered. Residual risk accepted for bounded isolated research, no capability claim.',rights_risk='Preserve separate original licenses/URLs/revisions/history/contributors and source archives. No known quoted/PI material admitted by filters+sample; unobserved exceptions remain possible. Complaints isolate provenance unit and future schedules.',no_new_TEST=True,admitted_sha256=hashlib.sha256((H/'admitted.jsonl.gz').read_bytes()).hexdigest())
 (H/'ADMISSION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report['splits'],ensure_ascii=False))
 # Fixed post-filter validation sample, no model outputs yet.
 more=[]
 seen={r['id']for r in sample}
 for source in ['jaquad','jawikibooks','jawikivoyage']:
  pool=[r for r in train if r['source']==source and r['id']not in seen];more+=sorted(pool,key=lambda r:hashlib.sha256(('validation|'+r['id']).encode()).hexdigest())[:4]
 (H/'quality-validation.json').write_text(json.dumps(more,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
