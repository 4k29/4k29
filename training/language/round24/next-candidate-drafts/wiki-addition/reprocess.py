"""Reproduce extraction from cached public revision responses; no new HTTP calls."""
import pathlib,json,hashlib,importlib.util,shutil,argparse,re,datetime
import collect as c
R=pathlib.Path(__file__).resolve().parent;B=c.B
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',type=pathlib.Path,required=True);a.add_argument('--out',type=pathlib.Path,required=True);args=a.parse_args();source=args.source;out=args.out;out.mkdir(exist_ok=False);p=read(R/'collection-policy.json');original=read(source/'manifest.json')
 shutil.copytree(source/'raw',out/'raw');shutil.copytree(source/'terms',out/'terms');shutil.copyfile(source/'license-records.json',out/'license-records.json')
 spec=importlib.util.spec_from_file_location('legacy',B/'round3/prepare.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
 sources=[];units=[]
 for line in (source/'source-documents.jsonl').read_text().splitlines():
  old=json.loads(line);raw=(source/old['rawFile']).read_bytes();wt=(source/old['wikitextFile']).read_text();assert sha(raw)==old['apiResponseSha256'] and sha(wt.encode())==old['wikitextSha256']
  blocks,reason=c.extract(wt,p);text='\n'.join(blocks);doc=dict(old,blocks=blocks,text=text,textSha256=sha(text.encode()),extractionExclusionReason=reason,processing=p['processing']+' Reject unsupported-tag/formula-dependent paragraphs and empty headings; do not fill missing prose.')
  sources.append(doc)
  if doc['partition']!='train':continue
  for start,end,t in legacy.chains(doc):
   if not p['minimumUnitCharacters']<=len(t)<=p['maximumUnitCharacters'] or len(re.findall('[ぁ-ゖァ-ヺ一-龯]',t))/len(t)<p['minimumJapaneseFraction'] or len(re.findall('[。！？]',t))<p['minimumSentenceTerminators']:continue
   assert t=='\n'.join(blocks[start:end]);did=doc['id']
   units.append(dict(doc,id=did+':unit:'+str(start),originalDocument=did,originalTextSha256=doc['textSha256'],unitKey=did+':chain:'+str(start),startLine=start,endLine=end,text=t,blocks=t.splitlines(),textSha256=sha(t.encode())))
 old=[json.loads(l) for l in (B/'round10/documents.jsonl').read_text().splitlines()];parts={x['document']:x['partition'] for x in read(B/'round10/split.json')['assignments']};held=[d['text'] for d in old if parts[d['id']]!='train'];train=[d['text'] for d in old if parts[d['id']]=='train'];old_held=len(held)
 for path in [B/'round18/sources/documents.jsonl',B/'round22/sources/source-documents.jsonl']:
  ds=[json.loads(l) for l in path.read_text().splitlines()];held.extend(d['text'] for d in ds if d['partition']=='reserved');train.extend(d['text'] for d in ds if d['partition']=='train')
 held.extend(d['text'] for d in sources if d['partition']=='reserved');wanted={d['text'][i:i+64] for d in units for i in range(len(d['text'])-63)};forbidden=set()
 for t in held+train:
  for i in range(max(0,len(t)-63)):
   g=t[i:i+64]
   if g in wanted:forbidden.add(g)
 admitted=[];excluded=[];seen=set()
 for d in units:
  grams={d['text'][i:i+64] for i in range(len(d['text'])-63)}
  if grams & (forbidden|seen):excluded.append(dict(unitKey=d['unitKey'],reason='64-character overlap with existing source, reserved source or earlier admitted TRAIN'));continue
  admitted.append(d);seen.update(grams)
 for name,rows in [('source-documents',sources),('documents',admitted)]:
  (out/(name+'.jsonl')).write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in rows))
 manifest=dict(original,reprocessedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),collectionPolicySha256=sha((R/'collection-policy.json').read_bytes()),collectorSha256=sha((R/'collect.py').read_bytes()),reprocessorSha256=sha(pathlib.Path(__file__).read_bytes()),reprocessedFromManifestSha256=sha((source/'manifest.json').read_bytes()),httpRequestsDuringReprocessing=0,admittedDocuments=len({d['originalDocument'] for d in admitted}),candidateTrainUnits=len(units),admittedUnits=len(admitted),admittedCharacters=sum(len(d['text']) for d in admitted),sourceDocumentsSha256=sha((out/'source-documents.jsonl').read_bytes()),documentsSha256=sha((out/'documents.jsonl').read_bytes()),excluded=excluded,existingNonTrainRawDocumentsAudited=old_held,experimentalOptimizerUpdates=0)
 manifest['minimumInterventionReached']=manifest['admittedDocuments']>=p['minimumTrainDocuments'] and len(admitted)>=p['minimumTrainUnits'] and manifest['admittedCharacters']>=p['minimumTrainCharacters'];write(out/'manifest.json',manifest);print(json.dumps({k:v for k,v in manifest.items() if k not in ['failures','excluded']}));assert manifest['minimumInterventionReached']
