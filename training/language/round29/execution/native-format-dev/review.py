"""Persist actually read unedited native DEV outputs and limited interpretation."""
import pathlib,json,hashlib,datetime,re
O=pathlib.Path(__file__).resolve().parent;read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();protocol=read(O/'protocol.json');names=['adopted25','human30round28','interim10round29'];reports={n:read(O/(n+'.json')) for n in names};manual={};lines=['# Additional native-format DEV — unabridged raw continuations','','Four source files / three unique openings. All openings are greetings. ExposedDEV, not TEST or a new gate. R25/R28 completed10000, R29 interimselected2000 fromretained2100; progress differs. Python-only on these openings; no parity claim.','']
for name,d in reports.items():
 assert d['protocolSha256']==sha(O/'protocol.json');rows=[]
 for r in d['rows']:
  assert r['validUtf8'] and r['validTokens'] and not r['eos'] and len(r['tokens'])==192
  local=(name=='adopted25' and r['id']=='native-dev-09119');loop=not local
  reason=('こたえの挿入、人口・人への局所再帰からQ見出しへ飛び、挨拶からの会話が成立しない。話題が変わる有限の局所反復としてprimaryでは長期周期ループと区別する。広いloop解釈の感度ではtrueでも全文不成立は不変。' if local else ('世界・人口の所有句を長く反復する。挨拶に続く会話が展開しない。' if name=='adopted25' and r['id']=='native-dev-04573' else '食べるので・食べるのですかを長く反復し、挨拶からの会話が成立しない。' if name=='adopted25' else '休みを尋ねるなど短い会話の形はあるが、お休みですね・お休みですかを長く繰り返して話題が進まない。' if name=='human30round28' else 'お願いしますを長く繰り返して挨拶から次の話題へ進まない。'))
  rows.append(dict(id=r['id'],fullContinuationCoherent=False,longLoopObserved=loop,eos=False,reason=reason))
 manual[name]=dict(generationSha256=sha(O/(name+'.json')),rows=rows,counts=dict(fullCoherent=0,longLoops=sum(r['longLoopObserved'] for r in rows),eos=0))
for i,p in enumerate(protocol['probes']):
 lines.extend(['## '+p['id'],'','Prefix:','```text',p['prefix'],'```'])
 for n,d in reports.items():
  r=d['rows'][i];assert all(r[k]==p[k] for k in ['id','prefix','sourceSha256','prefixSha256']);fence='`'*max(3,1+max((len(t) for t in re.findall(r'`+',r['text'])),default=0));lines.extend(['',n+':',fence+'text',r['text'],fence])
# Duplicate opening is preserved, never counted as4 independent contexts.
for d in reports.values():
 a,b=(r for r in d['rows'] if r['id'] in ['native-dev-12440','native-dev-12445']);assert a['prefix']==b['prefix'] and a['tokens']==b['tokens'] and a['text']==b['text']
result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='Assistant actually read all4 prefixes and all12 full unedited continuations; not independent human review',protocolSha256=sha(O/'protocol.json'),sourceFiles=4,uniqueRawSourceFiles=4,uniquePrefixTexts=3,allSelectedPrefixesAreGreetings=True,selectionNotChangedAfterSeeingThisLimitation=True,developmentOnly=True,newTestUsed=False,adoptionDecision=False,originalGatesChanged=False,models=manual,limitation='Small post-hoc diagnostic chosen after original daily failures; greeting-only/duplicate opening/content differs from role-labelled daily12; no causal role-label effect or broad conversation generalization claim. Different completed training progress across models. These openings have Python-only numerical evidence.',conclusion='All3 models fail full coherence even on native serialized human greetings. Human-data models produce recognizable conversational phrases but do not progress beyond repeated greetings/holiday questions. This does not identify EOS density as the cause.')
(O/'manual-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(O/'FULL_GENERATIONS.md').write_text('\n'.join(lines)+'\n');print(json.dumps({n:v['counts'] for n,v in manual.items()}))
