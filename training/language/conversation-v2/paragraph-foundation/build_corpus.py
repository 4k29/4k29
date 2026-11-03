"""Build reviewed original-paragraph condition and unused approved-caption control."""
import pathlib,json,gzip,hashlib,collections,sys,math
P=pathlib.Path(__file__).resolve().parent;OLD=pathlib.Path('/workspace/4k29/training/language/conversation-v2');sys.path.insert(0,str(P.parent));from new_tokenizer import Encoder
from schedule import references,batches,verify

def read(p):return json.loads(p.read_text())
def gzwrite(p,obj,lines=False):
 with p.open('wb')as raw:
  with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0)as f:
   if lines:
    for r in obj:f.write((json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode())
   else:f.write((json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n').encode())
def write(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
def main():
 assert not(P/'corpus.jsonl.gz').exists(),'Do not overwrite frozen corpus'
 decision=read(P/'ADMISSION_DECISION.json');assert decision['exploratory_research_gate_pass'];assert read(P/'SEMANTIC_REVIEW_SAMPLE.json')['extractor_sha256']==hashlib.sha256((P/'paragraphs.py').read_bytes()).hexdigest()
 enc=Encoder(read(P.parent/'data/tokenizer.json'));pieces=[bytes.fromhex(x)for x in enc.tok['bytes']]
 held=set(decision['held_unit_text_sha256']);b=[]
 for line in(P/'private/deduplicated-candidates.jsonl').read_text().splitlines():
  r=json.loads(line)
  if r['text_sha256']in held:continue
  tokens=enc(r['text']);assert len(tokens)==r['body_tokens'];assert b''.join(pieces[t]for t in tokens)==r['text'].encode()
  receipt=read(P/'private/discovery'/(r['source_cache'][:-3]+'.json'));assert receipt['sha256']==r['source_sha256']
  b.append(dict(id='env:'+r['source_cache']+':'+str(r['serial']),source='env_whitepaper',family='env-whitepaper-series',document_family=r['source_cache'],kind='official_multi_sentence_prose',text=r['text'],tokens=([1]if r['BOS']else[])+tokens+([2]if r['EOS']else[]),body_token_count=len(tokens),BOS=r['BOS'],EOS=r['EOS'],source_url=receipt['url'],source_sha256=r['source_sha256'],text_sha256=r['text_sha256'],heading=r['heading'],paragraph_indices=r['paragraph_indices'],license='PDL1.0 / CC-BY-4.0-compatible for provider-owned prose only',authorship='Official pre-2022 ministry prose; no human-only or fact-by-fact certification',processing='Original paragraph order preserved; display-whitespace extraction; omitted DOM is a barrier; no word repairs; source section boundary metadata preserved'))
 used=set();used_keys=set();images=set()
 with gzip.open(OLD/'modern-corpus/next-foundation/corpus.jsonl.gz','rt')as f:
  for line in f:
   r=json.loads(line)
   if r['source']=='stair':used.add(r['id']);used_keys.add(''.join(r['text'].split()).casefold());images.add(r['family'])
 held_ids={r['id']for r in read(OLD/'modern-corpus/STAIR_SPLIT_AUDIT.json')['held']};assert read(OLD/'modern-corpus/STAIR_PROSE_AUDIT_REVIEW.json')['research_component_quality_gate_pass'];a=[]
 with gzip.open(OLD/'modern-corpus/private/stair-prose-candidates.jsonl.gz','rt')as f:
  for line in f:
   r=json.loads(line)
   if r['split']!='train'or r['id']in held_ids or r['id']in used or ''.join(r['text'].split()).casefold()in used_keys:continue
   assert not r['hold_reasons'];assert b''.join(pieces[t]for t in r['body_tokens'])==r['text'].encode()
   a.append(dict(id=r['id'],source='stair_unused_annotation',family=r['image_family'],kind='human_caption_sentence',text=r['text'],tokens=[1]+r['body_tokens']+[2],body_token_count=len(r['body_tokens']),BOS=True,EOS=True,original_annotation_id=r['original_annotation_id'],original_image_id=r['original_image_id'],image_family_previously_seen=r['image_family']in images,license='CC-BY-4.0',source_archive_sha256=r['source_archive_sha256'],provenance_ref='modern-corpus/STAIR_LICENSE_RECEIPT.json + STAIR_ARCHIVE_RECEIPT.json + STAIR_SPLIT_AUDIT.json + STAIR_PROSE_AUDIT_REVIEW.json',processing='Original eligible finite caption; no punctuation/word repair. End means annotation unit, not paragraph or assistant turn.'))
 assert len(b)>=1000 and len({r['document_family']for r in b})>=100,'Insufficient diverse paragraph units for current preregistered exploration'
 corpus=sorted(a,key=lambda r:r['id'])+sorted(b,key=lambda r:r['id']);A=list(range(len(a)));B=list(range(len(a),len(corpus)));refs={arm:references(corpus,ix)for arm,ix in [('A',A),('B',B)]};available={arm:sum(r['length']-1 for r in rs)for arm,rs in refs.items()};budget=min(available.values());assert budget>=300000,'Insufficient independent teacher positions; no quota repetition'
 arms={arm:batches(corpus,refs[arm],budget)for arm in ['A','B']};audits={arm:verify(corpus,arms[arm])for arm in ['A','B']};assert audits['A']['target_counts']==audits['B']['target_counts'];assert all(x['max_padded_positions']<=4096 for x in audits.values()),'Padding resource bound requires new protocol, not silent rebatching'
 gzwrite(P/'corpus.jsonl.gz',corpus,True);gzwrite(P/'schedule.json.gz',dict(arms=arms,target_counts=audits['A']['target_counts'],budget=budget))
 result=dict(conditions={'A':'Unused already-eligible whole caption annotations, image families previously seen','B':'New licensed original environmental whitepaper continuous prose; no source corpus repetition'},pool_units={'A':len(a),'B':len(b)},pool_body_tokens={'A':sum(r['body_token_count']for r in a),'B':sum(r['body_token_count']for r in b)},available_teacher_positions=available,equal_processed_target_budget=budget,updates_per_arm=len(arms['A']),teacher_position_audit={k:{n:v for n,v in x.items()if n!='target_counts'}for k,x in audits.items()},B_original_documents=len({r['document_family']for r in b}),B_headings=len({r['heading']for r in b}),B_sources=1,B_family_policy='Entire Environment Ministry whitepaper series TRAIN only; entire Osaka source DEV only',A_previously_seen_image_family_annotations=sum(r['image_family_previously_seen']for r in a),B_units_context256_fit=sum(len(r['tokens'])<=257 for r in b),B_units_context256_overflow=sum(len(r['tokens'])>257 for r in b),B_body_tokens_new_vs_previous_TRAIN=sum(r['body_token_count']for r in b),limitations=['New prose remains government/environment genre, not diverse everyday voices','Character13gram duplicate detection does not prove semantic independence','Corpus pool tokens differ from actual processed target positions','Source, genre, length, BOS/EOS frequency and dropout shapes differ between data conditions; not a pure paragraph-length causal experiment'],full_bpe_byte_recovery=True,formal_adoption=False,optimizer_updates=0)
 write(P/'DATASET_AUDIT.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
