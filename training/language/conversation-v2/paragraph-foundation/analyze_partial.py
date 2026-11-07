"""Quarantined acquisition analysis; never implies TRAIN approval."""
import pathlib,json,gzip,hashlib,collections,sys
P=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent))
from new_tokenizer import Encoder
from paragraphs import Paragraphs,units
enc=Encoder(json.loads((P.parent/'data/tokenizer.json').read_text()))
by=collections.defaultdict(lambda:collections.Counter()); reasons=collections.Counter(); candidates=[]; seen=set()
for f in sorted((P/'private/discovery').glob('env-*-hj*.gz')):
 raw=gzip.decompress(f.read_bytes())
 try:text=raw.decode('utf-8')
 except UnicodeDecodeError:
  reasons['non_UTF8_requires_explicit_encoding_audit']+=1;continue
 parser=Paragraphs('main'if 'id="main"'in text else 'legacy_body');parser.feed(text);parser.finish();rows,why=units(parser.events);reasons.update(why)
 edition=f.name.split('-')[1];by[edition]['pages']+=1
 for row in rows:
  sha=hashlib.sha256(row['text'].encode()).hexdigest()
  if sha in seen:reasons['exact_duplicate_unit']+=1;continue
  seen.add(sha);tokens=enc(row['text']);assert b''.join(bytes.fromhex(enc.tok['bytes'][t])for t in tokens)==row['text'].encode()
  row.update(source_cache=f.name,source_sha256=hashlib.sha256(raw).hexdigest(),text_sha256=sha,body_tokens=len(tokens),sentences=row['text'].count('。'))
  candidates.append(row);by[edition].update(units=1,body_tokens=len(tokens),fits_context256=int(len(tokens)+2<=256),natural_section_ends=int(row['EOS']))
(P/'private/paragraph-candidates.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in candidates))
report=dict(status='QUARANTINED: semantic review, near-duplicate and split audits pending',admitted_tokens=0,editions=dict(by),exclusions=dict(reasons),candidate_units=len(candidates),candidate_body_tokens=sum(x['body_tokens']for x in candidates))
(P/'PARTIAL_EXTRACTION_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
