"""Reparse every accepted original HTML archive without refetching."""
import gzip,hashlib,json,pathlib
from collect import parse,selected,canonical
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 docs=[json.loads(l) for l in (ROOT/'documents.jsonl').read_text().splitlines()];meta=read(ROOT/'sources.json');credits={c['id']:c for c in meta['sources']};urls=set();texts=set()
 assert meta['collectorSourceSha256']==sha((ROOT/'collect.py').read_bytes());assert meta['actualOptimizerUpdates']==0 and not meta['tokenizerTraining']
 for d in docs:
  raw=gzip.decompress((ROOT/d['htmlArchive']).read_bytes());assert sha(raw)==d['htmlSha256']==credits[d['id']]['htmlSha256']
  p,encoding=parse(raw);blocks,skip=selected(p);assert skip is None and blocks==d['blocks'] and encoding==d['encoding']
  text='\n'.join(b['text'] for b in blocks);assert text==d['text'] and sha(text.encode())==d['textSha256']==credits[d['id']]['textSha256']
  assert all(b['tag']=='p' and len(b['text'])>=40 for b in blocks) and len({b['originalBlockIndex'] for b in blocks})==len(blocks)
  assert canonical(d['url']) not in urls and d['textSha256'] not in texts;urls.add(canonical(d['url']));texts.add(d['textSha256'])
 assert meta['documents']==len(docs)==len(credits) and meta['characters']==sum(len(d['text']) for d in docs) and meta['utf8Bytes']==sum(len(d['text'].encode()) for d in docs)
 attempts=read(ROOT/'attempts.json');assert attempts['allFailuresAndSkipsRetained']
 accepted=[a for a in attempts['attempts'] if a.get('accepted')];assert {a['id'] for a in accepted}==set(credits) and len(accepted)==len(docs)
 report=dict(allArchivesReparsed=True,htmlAndTextHashesVerified=True,wholeOriginalParagraphsVerified=True,documents=len(docs),characters=meta['characters'],utf8Bytes=meta['utf8Bytes'],collectorSourceSha256=meta['collectorSourceSha256'],verificationSourceSha256=sha(pathlib.Path(__file__).read_bytes()),actualOptimizerUpdates=0,tokenizerTraining=False)
 (ROOT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
