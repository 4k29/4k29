"""Build isolated QA candidates from the fixed acquisition selection; not TRAIN adoption."""
import pathlib,json,hashlib,gzip,sys,re,collections
from maff_extract import Article
D=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(D.parent));from new_tokenizer import Encoder

def main():
 enc=Encoder(json.loads((D.parent/'data/tokenizer.json').read_text()));pieces=[bytes.fromhex(s)for s in enc.tok['bytes']];selection=json.loads((D/'MAFF_EXPANSION_SELECTION.json').read_text())['selected'];rows=[];missing=[];counts=collections.Counter();old={r['provenance']['url']for r in map(json.loads,gzip.open(D.parent/'diverse-foundation/future-sources/maff/candidates.private.jsonl.gz','rt'))}
 for row in selection:
  u=row['url'];ident=hashlib.sha256(u.encode()).hexdigest()[:20];path=D/'private/maff-expanded'/f'{ident}.html.gz';rp=path.with_name(ident+'.receipt.json')
  if not path.exists():missing.append(u);continue
  receipt=json.loads(rp.read_text());raw=gzip.decompress(path.read_bytes());assert hashlib.sha256(raw).hexdigest()==receipt['sha256'];a=Article();a.feed(raw.decode('utf-8'));text=a.title+'\n'+'\n'.join(a.paragraphs);ids=enc(text);assert b''.join(pieces[t]for t in ids)==text.encode();holds=[]
  if not a.title or not a.paragraphs or not text.endswith(('。','？','！')):holds.append('incomplete_or_unconfirmed_answer_end')
  if re.search(r'図[0-9１２３]|下の図|下の表|写真|著作|転載|引用|図を|をご覧|こちら|次のとおり',text):holds.append('figure_external_or_third_party_dependency')
  if re.search(r'病気|食中毒|アレルギ|医療|治療|農薬|発がん',text):holds.append('health_or_safety_fact_review')
  rows.append(dict(id='maff:'+ident,url=u,category=row['category'],title=a.title,text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),source_sha256=receipt['sha256'],body_token_count=len(ids),prior54_overlap=u in old,acquisition=receipt['acquisition'],hold_reasons=holds,EOS_approved=False,admission='quarantined candidate'))
  counts['body_tokens']+=len(ids);counts['overlap_prior54']+=u in old;counts['beyond_prior54']+=u not in old;counts['new_HTTP_answer_texts']+=receipt['acquisition']=='new HTTP'
 with gzip.open(D/'private/maff-expanded-candidates.jsonl.gz','wt')as f:
  for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 summary=dict(extracted_pages=len(rows),selected_pages=len(selection),missing=len(missing),counts=dict(counts),byte_roundtrip=True,admitted_tokens=0,optimizer_updates=0,warning='In-progress acquisition snapshot. New network text != independent qualified TRAIN. Factual validity and full answer completeness require review.')
 (D/'MAFF_EXPANSION_EXTRACTION.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
if __name__=='__main__':main()
