"""Prepare additional licensed candidates only; never auto-admit or train them."""
import collections,gzip,re
from common import *
from prepare import rank
import importlib.util
spec=importlib.util.spec_from_file_location('prior_admission',H/'prepare.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)

def main():
 corpus=V/'foundation-data/corpus/documents.jsonl.gz';old=list(map(json.loads,gzip.open(H/'data.jsonl.gz','rt')));old_ids={r['provenance']['id']for r in old};old_dev_components={r['component']for r in old if r['split']=='dev'};candidates=[];reasons=collections.Counter();seen=set()
 for doc in map(json.loads,gzip.open(corpus,'rt')):
  if doc['split']!='train'or doc['source']!='jaquad'or doc['id']in old_ids:continue
  if doc['component']in old_dev_components:raise AssertionError('Existing DEV leakage')
  if prior.BAD_TITLE.search(doc['title']):continue
  if doc['license']!='CC-BY-SA-3.0':raise AssertionError('Unexpected license')
  for p in doc['paragraphs']:
   if not p['keepForCandidateTraining']:continue
   text=p['normalizedText'];reason=prior.eligible(text)
   if reason:reasons[reason]+=1;continue
   key=''.join(text.split())
   if key in seen:reasons['exact_canonical_duplicate']+=1;continue
   seen.add(key);candidates.append(dict(id=doc['id']+':'+str(p['ordinal']),component=doc['component'],title=doc['title'],text=text,previous_own_BPE_tokens=p['ownBpeTokens'],provenance={k:v for k,v in doc.items()if k not in ['paragraphs','extractionCounts']},paragraph_ordinal=p['ordinal'],BOS=False,EOS=False,status='additional_candidate_only_NOT_admitted_or_trained'))
 chosen=[];family=collections.Counter();total=0
 for r in sorted(candidates,key=lambda r:rank('expanded-source|'+r['id'])):
  n=r['previous_own_BPE_tokens']
  if total+n>2_000_000 or family[r['component']]+n>100_000:continue
  chosen.append(r);family[r['component']]+=n;total+=n
 with(N/'expansion-broad-candidates.jsonl.gz').open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:
   for r in chosen:z.write((json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 report=dict(source_corpus_sha256=sha(corpus),candidate_file_sha256=sha(N/'expansion-broad-candidates.jsonl.gz'),new_source_acquisition=0,additional_candidate_paragraphs=len(chosen),candidate_prior_BPE_tokens=total,candidate_components=len(family),form='JaQuAD original excerpts, never add EOS/BOS',admitted_tokens=0,trained_tokens=0,status='Prepared only; no semantic sample admission or full retokenization yet; not safe to label TRAIN ready',prior_rights_pipeline_reused=True,old_PR101_document_ids_excluded=True,existing_DEV_components_excluded=True,sealed_TEST_used=False,reasons=dict(reasons),next='Only after generation improvement: fixed source sample review, full BPE byte roundtrip/independent-volume checks, split/near-duplicate audit, fixed multi-million-token schedule/resource plan before any expansion update');write(N/'EXPANSION_BROAD_STATUS.json',report);print(report)
if __name__=='__main__':main()
