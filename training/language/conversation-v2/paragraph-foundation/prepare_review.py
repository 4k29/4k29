"""One fixed full-corpus review sample; no model output involved."""
import pathlib,json,sys,hashlib,collections,subprocess
P=pathlib.Path(__file__).resolve().parent
from deduplicate import deduplicate
from cross_audit import audit

def write(path,r):path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
def main():
 status=json.loads((P/'ACQUISITION_STATUS.json').read_text());assert status['complete']and status['successful']==status['selected'],'Acquisition not complete'
 assert not(P/'SEMANTIC_REVIEW_SAMPLE.json').exists(),'No implicit resampling'
 subprocess.run([sys.executable,str(P/'analyze_partial.py')],check=True,stdout=subprocess.DEVNULL)
 rows=[json.loads(l)for l in(P/'private/paragraph-candidates.jsonl').read_text().splitlines()];clean,held=deduplicate(rows);clean,cross,method=audit(clean)
 (P/'private/deduplicated-candidates.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in clean));write(P/'DUPLICATE_AUDIT.json',dict(input_units=len(rows),remaining_units=len(clean),remaining_body_tokens=sum(r['body_tokens']for r in clean),internal_held=held,cross_held=cross,method=method,admitted_tokens=0))
 strata=collections.defaultdict(list)
 for r in clean:strata[(r['source_cache'].split('-')[1],'short'if r['body_tokens']<=256 else'long')].append(r)
 selected=[];counts={}
 for key,rs in sorted(strata.items()):
  rs.sort(key=lambda r:hashlib.sha256(('paragraph-semantic-audit-v1|'+r['text_sha256']).encode()).hexdigest());selected.extend(rs[:2]);counts['|'.join(key)]=min(2,len(rs))
 assert len(selected)==32,('Insufficient full audit sample',counts)
 write(P/'private/semantic-review-sample.json',dict(rows=selected));write(P/'SEMANTIC_REVIEW_SAMPLE.json',dict(status='Fixed before semantic reading and model outputs; pending',rows=[{k:r[k]for k in ['source_cache','source_sha256','text_sha256','paragraph_indices','body_tokens','BOS','EOS']}for r in selected],strata=counts,full_private_sample_sha256=hashlib.sha256((P/'private/semantic-review-sample.json').read_bytes()).hexdigest(),extractor_sha256=hashlib.sha256((P/'paragraphs.py').read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256((P/'QUALITY_REVIEW_PROTOCOL.json').read_bytes()).hexdigest(),independent_human_evaluation=False))
 print(json.dumps(dict(sampled_units=len(selected),candidate_units=len(clean),candidate_body_tokens=sum(r['body_tokens']for r in clean),admitted_tokens=0)))
if __name__=='__main__':main()
