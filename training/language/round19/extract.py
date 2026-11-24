"""Recover existing TRAIN-only original chains before reference headers.
Original text, licenses and folds retained. No fetching, rewriting or teacher.
"""
import pathlib,json,hashlib,importlib.util,datetime
R=pathlib.Path(__file__).resolve().parent;B=R.parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 out=R/'sources';out.mkdir(exist_ok=False)
 spec=importlib.util.spec_from_file_location('legacy_chain',B/'round3/prepare.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
 docs=[json.loads(l) for l in (B/'round10/documents.jsonl').read_text().splitlines()];parts={x['document']:x['partition'] for x in read(B/'round10/split.json')['assignments']};units=read(B/'round10/units.json');oldtext={}
 for u in units:
  if u['partition']=='train':oldtext.setdefault(u['document'],set()).add(u['text'])
 held=[d for d in docs if parts[d['id']]!='train'];candidates=[]
 for d in docs:
  if d['site']!='maff' or parts[d['id']]!='train':continue
  lines=d['text'].splitlines();cut=next((i for i,l in enumerate(lines) if l.strip() in ['参考資料','参考文献','出典']),len(lines))
  for a,b,t in legacy.chains(dict(d,text='\n'.join(lines[:cut]))):
   if t in oldtext.get(d['id'],set()):continue
   assert t=='\n'.join(lines[a:b]);key=d['id']+':chain:'+str(a);assert not any(u['document']==d['id'] and u['startLine']==a for u in units if u['partition']=='train')
   candidates.append(dict(id=d['id']+':recovered:'+str(a),originalDocument=d['id'],startLine=a,endLine=b,site='maff',partition='train',url=d['url'],title=d['title'],author=d['author'],license=d['license'],licenseUrl=d['licenseUrl'],policyUrl=d['policyUrl'],attribution=d.get('attribution',f"出典：{d['author']}ウェブサイト（{d['url']}）を加工して作成")+'（既存TRAIN原文を参考資料より前で切り出し）',originalTextSha256=d['textSha256'],text=t,textSha256=hashlib.sha256(t.encode()).hexdigest(),blocks=t.splitlines(),unitKey=key))
 wanted={d['text'][i:i+64] for d in candidates for i in range(max(0,len(d['text'])-63))};bad=set()
 for d in held:
  for i in range(max(0,len(d['text'])-63)):
   t=d['text'][i:i+64]
   if t in wanted:bad.add(t)
 admitted=[];excluded=[]
 for d in candidates:
  hits=[hashlib.sha256(t.encode()).hexdigest() for t in bad if t in d['text']]
  if hits:excluded.append({'unitKey':d['unitKey'],'spanSha256':sorted(hits),'reason':'64-character exact match with existing non-TRAIN raw text'})
  else:admitted.append(d)
 (out/'documents.jsonl').write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in admitted))
 policies=read(B/'round2/modern-sources.json')['policies'];write(out/'license-records.json',{'source':'../round2/modern-sources.json','sourceSha256':sha(B/'round2/modern-sources.json'),'policies':policies,'note':'Unchanged captured license records; each recovered unit retains its original author/license/attribution fields.'})
 manifest=dict(retrievedAt=None,derivedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),sourceKind='Existing archived human government explanatory/FAQ prose; no new fetch',sourceDocumentsSha256=sha(B/'round10/documents.jsonl'),sourceSplitSha256=sha(B/'round10/split.json'),sourceUnitsSha256=sha(B/'round10/units.json'),legacyChainCodeSha256=sha(B/'round3/prepare.py'),licenseRecordsSha256=sha(out/'license-records.json'),candidateUnits=len(candidates),candidateCharacters=sum(len(d['text']) for d in candidates),admittedUnits=len(admitted),admittedCharacters=sum(len(d['text']) for d in admitted),admittedSourceDocuments=len({d['originalDocument'] for d in admitted}),existingHeldRawDocumentsAudited=len(held),excluded=excluded,allSourcesAlreadyTrain=True,originalTextExact=True,testReadForDuplicateAudit=True,testScoredOrGenerated=False,foldsChanged=False)
 write(out/'manifest.json',manifest);print(json.dumps({k:v for k,v in manifest.items() if k!='excluded'}));assert len(admitted)>=10
