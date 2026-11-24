"""Versioned pretraining bug repair; retain the exact fixed32 original text sample."""
import pathlib,json,subprocess,sys,hashlib,shutil
from deduplicate import deduplicate
from cross_audit import audit
P=pathlib.Path(__file__).resolve().parent

def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 assert not(P/'PLAN.json').exists(),'Repair only before scientific plan/training'
 old=[json.loads(l)for l in(P/'private/deduplicated-candidates.jsonl').read_text().splitlines()];old_sample=json.loads((P/'private/semantic-review-sample-v1.json').read_text())['rows']
 subprocess.run([sys.executable,str(P/'analyze_partial.py')],check=True,stdout=subprocess.DEVNULL);rows=[json.loads(l)for l in(P/'private/paragraph-candidates.jsonl').read_text().splitlines()];clean,held=deduplicate(rows);clean,cross,method=audit(clean)
 key=lambda r:(r['source_cache'],r['serial'],r['text_sha256']);assert {key(r)for r in old}=={key(r)for r in clean},'Unexpected text-selection change'
 current={key(r):r for r in clean};sample=[current[key(r)]for r in old_sample];assert [r['text_sha256']for r in sample]==[r['text_sha256']for r in old_sample]
 changed=[dict(source_cache=r['source_cache'],serial=r['serial'],text_sha256=r['text_sha256'],old_EOS=r['EOS'],new_EOS=current[key(r)]['EOS'])for r in old if r['EOS']!=current[key(r)]['EOS']];assert all(r['old_EOS']and not r['new_EOS']for r in changed)
 (P/'private/deduplicated-candidates.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in clean));write(P/'private/semantic-review-sample.json',dict(rows=sample));sample_meta=json.loads((P/'SEMANTIC_REVIEW_SAMPLE.json').read_text());sample_meta.update(version=2,original_fixed_text_selection_retained=True,rows=[{k:r[k]for k in ['source_cache','source_sha256','text_sha256','paragraph_indices','body_tokens','BOS','EOS']}for r in sample],full_private_sample_sha256=hashlib.sha256((P/'private/semantic-review-sample.json').read_bytes()).hexdigest(),extractor_sha256=hashlib.sha256((P/'paragraphs.py').read_bytes()).hexdigest())
 protocol=json.loads((P/'QUALITY_REVIEW_PROTOCOL.json').read_text());protocol.update(version=2,extractor_sha256=sample_meta['extractor_sha256'],criteria_unchanged=True,original_sample_texts_unchanged=True,repair='Remove EOS at parent-heading to child-heading transitions. Do not resample or relax gate.')
 write(P/'QUALITY_REVIEW_PROTOCOL.json',protocol);sample_meta['protocol_sha256']=hashlib.sha256((P/'QUALITY_REVIEW_PROTOCOL.json').read_bytes()).hexdigest();write(P/'SEMANTIC_REVIEW_SAMPLE.json',sample_meta)
 write(P/'DUPLICATE_AUDIT.json',dict(input_units=len(rows),remaining_units=len(clean),remaining_body_tokens=sum(r['body_tokens']for r in clean),internal_held=held,cross_held=cross,method=method,admitted_tokens=0,version=2,text_selection_unchanged=True))
 write(P/'BOUNDARY_IMPLEMENTATION_REPAIR.json',dict(v1_admission='No-Go: EOS hierarchy implementation issue found before paragraph training',v2_repair='Heading hierarchy respected; deeper child heading does not terminate parent introduction',changed_units=changed,removed_EOS_teachers=len(changed),added_EOS_teachers=0,source_words_order_and_sample_unchanged=True,criteria_unchanged=True,paragraph_training_updates=0,prior_execution_validation_calls=6,impact='New paragraph extractor only; PR105 and earlier outputs/checkpoints unaffected. Frozen Osaka DEV prefixes/texts unchanged; their EOS flags were already false.'))
 print(json.dumps(dict(removed_EOS=len(changed),sample_texts_unchanged=True,candidate_units=len(clean),body_tokens=sum(r['body_tokens']for r in clean))))
if __name__=='__main__':main()
