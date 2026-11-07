"""Persist the main assistant's full reading decisions; no automated semantic scoring."""
import pathlib,json,collections,hashlib
P=pathlib.Path(__file__).resolve().parent
# These reasons are authored after reading all32 fixed complete source units.
REASONS=[
('accept','Dated2008 policy explanation; three connected provisions/implementation sentences. Dense administrative style, not everyday conversation. No omitted chart/quotation needed.'),
('accept','Connected historical narrative from Earth/life to human civilization. Scientific timescales are explicitly approximate/as-of2010 source, not newly verified current facts.'),
('hold','Footnote starts（注）（3） and refers to a missing survey subsection. Not a self-contained explanation despite enough Japanese period marks.'),
('accept','Defines waste, exceptions and classification in connected explanatory prose. Dated legal description, not a current legal-advice response.'),
('accept','Defines two initiatives, their purposes, activities and Japanese involvement. Initial IPBES/GBIF acronyms are background, not missing answer evidence; source-date2012 retained.'),
('hold','以上のデータ refers to omitted data necessary for its claimed inference. Do not treat it as independent evidence-complete prose.'),
('accept','Related ship/aircraft emission-rule explanations are understandable as historical2012 prose. Legal abbreviation periods are not additional true sentences.'),
('accept','Defines material flow, inputs/outputs and its purpose; three connected sentences with an explicit topic.'),
('accept','Connected food-recycling policy, targets and review chronology; dated2014 account. Administrative distribution bias noted.'),
('accept','Names a reconstruction plan, explains its purpose, examples and2040 goal. Goal is explicitly aspirational, not a fulfilled fact.'),
('accept','Defines relevant committee and describes two related investigation activities. Legal citation punctuation is not extra sentences; usable two-sentence prose.'),
('accept','States support need, fund response and concrete implementation; references are internally intelligible, dated2014 institutions.'),
('accept','Substantial connected cause/explanation about3R, materials, energy and emissions, with caveats. General claims not presented as newly independently fact-checked; original2016 source.'),
('accept','Defines monitoring targets/method, then dates and broad results.それまで refers to described historical monitoring, not an omitted diagram dependency.'),
('accept','Explains construction recycling law scope and registration; coherent three-sentence dated legal exposition, not a current compliance answer.'),
('accept','Water monitoring framework and later radioactivity monitoring are connected; source2016 dates explicit.'),
('accept','Related transport/logistics measures follow one topic; long administrative paragraph remains grammatical. Policy-list style is a corpus limitation.'),
('accept','Explains limits of closed regional economies and complementary urban/rural resource networks.重点戦略 is background reference; central reasoning and definition are present.'),
('accept','Defines off-road vehicles/rule and a support measure. Legal citation periods overcount sentences; two actual connected sentences are usable historical prose.'),
('accept','Explains a platform, associated scientific panel and forum with dates.2018 prospective publication remains a dated source statement, not asserted current status.'),
('accept','Coherent policy reasoning on reducing single-use plastics, incentives, alternatives and reuse. Normative/policy tone recorded, not assistant identity.'),
('accept','Explains climate-adaptation support and a multi-region2017 project with mechanism; climate topic becomes explicit within the complete unit.'),
('accept','States ODA framework, environmental concern and island-state needs; dated policy prose, no personal attributes.'),
('accept_conditional_dated_prose','Typhoon impacts and waste-support actions are internally connected. Event year is not in the unit;2019 report/source metadata must be retained. Usable as historical language material only, not standalone current factual QA or a year-specific answer.'),
('accept','Named G20 Osaka summit identifies the event; explains commitments and follow-up. Dates/report2020 retained; source-owned summary, no long third-party quotation.'),
('accept','Rural resources, policy and need for cross-sector cooperation form a connected explanation. Source2020 ministry prose, no direct third-party reproduction evident.'),
('hold','Ends by promising a following chronological introduction; child-section content is absent. Not a completed standalone explanation; hierarchy EOS is removed in v2.'),
('accept','Related environmental-information support mechanisms; acronyms GEOC/EPO are not expanded here, so accessibility is limited, but connected activity description remains intelligible.'),
('accept','Introduces environmental taxation, mechanism, phased timing and revenue use. Numerical tax claim is a dated official2021 statement, not independently audited current law.'),
('accept','Connects changing resource use, habitat-management loss, examples and remedial activity; explicit causal progression.'),
('accept','Odor-law measures, training and qualification examination are connected dated2020 activities. Citation periods are not extra semantic sentences.'),
('hold','Says 以下の5つのアクション but omits the actual actions. Keep the entire affected source subsection out; do not invent or repair the list.')]

def main():
 sample=json.loads((P/'private/semantic-review-sample.json').read_text())['rows'];assert len(sample)==len(REASONS)==32
 rows=[];families=set()
 for i,(r,(decision,reason))in enumerate(zip(sample,REASONS)):
  row=dict(index=i,text_sha256=r['text_sha256'],source_cache=r['source_cache'],heading=r['heading'],decision=decision,reason=reason,full_unit_read=True,reviewer='main assistant only; not independent human evaluator',facts='Official dated source attribution retained; no claim of independent fact-by-fact verification',rights_privacy='No unhandled severe rights/privacy/corruption identified in this unit; source-owned scoped prose only',BOS=r['BOS'],EOS=r['EOS']);rows.append(row)
  if decision=='hold':families.add((r['source_cache'],r['heading']))
 allrows=[json.loads(l)for l in(P/'private/deduplicated-candidates.jsonl').read_text().splitlines()];held=[r for r in allrows if(r['source_cache'],r['heading'])in families];usable=sum(r['decision'].startswith('accept')for r in rows);passed=usable>=28
 review=dict(version=2,source_sample_sha256=hashlib.sha256((P/'private/semantic-review-sample.json').read_bytes()).hexdigest(),reviewed=32,usable=usable,held_sample=32-usable,minimum_usable_fixed_before_reading=28,unhandled_severe_rights_privacy_corruption=0,criteria_unchanged=True,original_fixed_sample_texts_unchanged=True,review_gate_pass=passed,rows=rows,limitations=['Single assistant review; no independent human/native-speaker evaluation','Official authorship and dated facts are not human-only or independently fact-checked certifications','Government/policy/technical style remains dominant; not everyday conversational data','Period marks inside legal abbreviations overcount semantic sentences; actual reading, not punctuation count, determines usability'])
 (P/'SEMANTIC_REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
 decision=dict(exploratory_research_gate_pass=passed,formal_adoption=False,held_source_heading_families=[dict(source_cache=s,heading=h)for s,h in sorted(families)],held_unit_text_sha256=[r['text_sha256']for r in held],held_units=len(held),held_body_tokens=sum(r['body_tokens']for r in held),reviewed_usable=usable,reviewed_total=32,admitted_candidate_units=len(allrows)-len(held),admitted_candidate_body_tokens=sum(r['body_tokens']for r in allrows if r['text_sha256']not in{h['text_sha256']for h in held}),boundary_v1='No-Go repaired and separately recorded; no old experiment invalidated',purpose='Bounded exploratory pretraining on source-owned dated prose only, not current factual assistant-response training',proofs=['SOURCE_RIGHTS_DECISION.json','BOUNDARY_IMPLEMENTATION_REPAIR.json','DUPLICATE_AUDIT.json','SEMANTIC_REVIEW.json'],no_claim_all_source_quality_certified=True)
 (P/'ADMISSION_DECISION.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in decision.items()if k not in ['held_unit_text_sha256','held_source_heading_families']},ensure_ascii=False))
if __name__=='__main__':main()
