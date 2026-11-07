"""Read-only source/dependency integrity checks before zero-update model profiling."""
import argparse,gzip,json,pathlib,sys
from build import BASE,book_family,canonical,norm,sha_bytes,sha_file,write
HERE=pathlib.Path(__file__).resolve().parent
def verify(a):
 evidence=[]
 for name in ['jaquad','jawikibooks','jawikivoyage']:
  mpath=pathlib.Path('/dev/shm/foundation-data-source')/name/'manifest.json';m=json.loads(mpath.read_text())
  files=m['shards']if name=='jaquad'else [dict(rawPath=m['path'],sha256=m['sha256'],bytes=m['bytes'])]
  for row in files:
   path=pathlib.Path(row['rawPath']);assert path.stat().st_size==row['bytes'] and sha_file(path)==row['sha256']
  evidence.append(dict(source=name,manifestSha256=sha_file(mpath),rawFiles=len(files),rawBytes=sum(x['bytes']for x in files),allSourceBytesVerified=True))
 for name in ['jawikibooks','jawikivoyage']:
  receipt=json.loads((pathlib.Path('/dev/shm/foundation-data-build')/name/'receipt.json').read_text())
  for row in receipt['files']:
   path=pathlib.Path(row['path']);assert path.stat().st_size==row['bytes'] and sha_file(path)==row['sha256']
  evidence.append(dict(derivedSource=name,adapterSha256=receipt['adapterSha256'],parser=receipt['parser'],allRawWikitextAndDerivedArchivesVerified=True,
   derivedArchive=next(x for x in receipt['files']if pathlib.Path(x['path']).name=='derived-pages.jsonl.gz')))
 receipt=json.loads((a.input/'receipt.json').read_text())
 for row in receipt['files']:
  path=pathlib.Path(row['path']);assert path.stat().st_size==row['bytes'] and sha_file(path)==row['sha256']
 families={};components={};ids=set();doc_count=para_count=0;raw_counts={};kept={};counts={}
 with gzip.open(a.input/'documents.jsonl.gz','rt')as f:
  for line in f:
   d=json.loads(line);assert d['id']not in ids;ids.add(d['id']);doc_count+=1
   families.setdefault(d['family'],set()).add(d['split']);components.setdefault(d['component'],set()).add(d['split'])
   if d['source']=='jawikibooks':assert d['family']=='jawikibooks|'+book_family(d['title'])
   for p in d['paragraphs']:
    para_count+=1;t=p['text'];assert norm(t)==p['normalizedText'];assert sha_bytes(t.encode())==p['rawTextSha256'];assert sha_bytes(canonical(t).encode())==p['canonicalSha256']
    for q in p.get('qas',[]):
     for answer in q['answers']:assert t[answer['answer_start']:answer['answer_start']+len(answer['text'])]==answer['text']
    if p['keepForCandidateTraining']:
     assert p['canonicalSha256']not in kept,'Unremoved canonical duplicate';kept[p['canonicalSha256']]=d['split']
     counts[d['split']]=counts.get(d['split'],0)+p['ownBpeTokens']
 assert all(len(s)==1 for s in families.values())and all(len(s)==1 for s in components.values())
 assert doc_count==receipt['totalRawDocuments'] and para_count==receipt['totalRawParagraphs']
 assert counts=={k:v['retainedOwnBpeBodyTokens']for k,v in receipt['splitStats'].items()if v['retainedOwnBpeBodyTokens']}
 codepaths=[HERE/'build.py',HERE/'post_audit.py',HERE/'wiki_adapter.py',HERE/'verify_inputs.py',BASE/'new_tokenizer.py',BASE/'data/tokenizer.json',BASE.parents[2]/'training/dialogue/tokenizer.py',BASE.parents[2]/'training/language/round10/word_bpe.py']
 result=dict(passed=True,sourceEvidence=evidence,dependencySha256={str(p):sha_file(p)for p in codepaths},
  documents=doc_count,paragraphs=para_count,retainedCanonicalParagraphs=len(kept),splitBodyTokens=counts,
  familyAndDuplicateComponentsNeverCrossSplit=True,allScopedNumberedSectionFamiliesCanonical=True,
  originalQaOffsetsPreserved=True,normalizationDerivedOnly=True,allCandidateUnadmitted=True,
  semanticOrGeographicFamilyDisjointnessProven=False,humanOnlyCertified=False,optimizerUpdates=0,modelObjectsCreated=0,testUsed=False)
 write(a.output,result);print(json.dumps({k:v for k,v in result.items()if k not in ['sourceEvidence','dependencySha256']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);verify(p.parse_args())
