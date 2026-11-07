"""Offline verification of actual TRAIN caption leakage; no model or image fetch."""
import pathlib,json,hashlib,numpy as np,importlib.util
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';repo=R.parents[2];O=E/'jma-notice-provenance';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=read(E/'generated-notice-train-match-audit.json');audit=read(O/'audit.json');index=read(R/'multiview/train.index.json');tok=read(R/'multiview/tokenizer.json');pieces=[bytes.fromhex(s)for s in tok['bytes']];values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');matches=[];count=0
assert sha(R/'multiview/train.tokens.bin')==index['tokensSha256']
for r in index['documents']:
 if r['variant']!=0 or r['site']=='human-chat':continue
 count+=1;raw=b''.join(pieces[int(t)]for t in values[r['offset']:r['offset']+r['length']]if int(t)>=6);text=raw.decode('utf8')
 if '商用利用不可'in text or 'Yahoo!ニュース制作図解'in text:matches.append(dict(id=r['id'],sourceDocument=r['sourceDocument'],site=r['site'],decodedTextSha256=hashlib.sha256(raw).hexdigest(),matchingLines=[s for s in text.splitlines()if '商用利用不可'in s or 'Yahoo!ニュース制作図解'in s]))
assert count==expected['admittedTrainCanonicalOldUnitsChecked']and matches==expected['matches']
collector=repo/'training/dialogue/collect_web_language.py';assert sha(collector)==audit['collectorSha256'];assert sha(R.parent/'round3/collect_weather.py')==audit['weatherCollectorSha256']
spec=importlib.util.spec_from_file_location('original_text_collector',collector);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for row in audit['sources']:
 p=O/(row['id'].split(':')[-1]+'.html');assert sha(p)==row['htmlSha256']==row['capturedHtmlSha256']and row['exactHistoricalHtmlMatch']
 parser=m.Page();parser.feed(p.read_text());paragraphs={b['text']for b in parser.blocks if b['tag']=='p'}
 for match in matches:
  if match['sourceDocument']==row['id']:assert all(line in paragraphs for line in match['matchingLines'])
probe=m.Page();probe.feed('<main><p><img src="unused.png" alt="UNIQUE_IMAGE_ALT_NOT_TEXT">visible text only</p></main>');assert all('UNIQUE_IMAGE_ALT_NOT_TEXT'not in b['text']for b in probe.blocks)
print(json.dumps(dict(admittedTrainCanonicalUnits=count,matchedTrainUnits=len(matches),exactHistoricalHtmlSources=len(audit['sources']),captionNoticeTextVerified=True,imageAltNotExtracted=True,noImageOrOcrInput=True,noModelForwardOrOptimizer=True,additionalOptimizerUpdates=0)))
