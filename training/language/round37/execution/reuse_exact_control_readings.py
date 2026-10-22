"""Reuse historical control readings only after exact current full-core equality; no new grade."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round36/execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();keys=['id','prefix','text','tokens','eos','validUtf8','validTokens','inputTokens'];records=[]
for g,m in [('daily-new-python.json','daily-new-reading.json'),('content-native-dev/new-python.json','content-native-dev/new-reading.json'),('fixed-source-mrmp-dev/new-python.json','fixed-source-mrmp-dev/new-reading.json')]:
 old=E/g.replace('new-','old-');a,b=read(old),read(P/g);assert len(a['rows'])==len(b['rows'])
 assert all(all(x[k]==y[k]for k in keys)for x,y in zip(a['rows'],b['rows'],strict=True))
 manual=read(P/m);manual.update(generationSha256=sha(old),priorReadingPath=str((P/m).relative_to(R.parent)),priorReadingSha256=sha(P/m),exactPriorFullCoreIdentityVerified=True,notFreshReadingClaim=True,originalReviewer=manual['reviewer'],reviewer='Prior Round36 actual full reading reused after exact current control full-core identity; not fresh reading')
 out=E/m.replace('new-','old-');out.write_text(json.dumps(manual,ensure_ascii=False,indent=2)+'\n');records.append(dict(controlGeneration=str(old.relative_to(R)),priorGeneration=str((P/g).relative_to(R.parent)),allRowsExactFullCoreIdentity=True,priorReadingSha256=sha(P/m),currentBoundReadingSha256=sha(out),notFreshReadingClaim=True))
(E/'old-control-reading-provenance.json').write_text(json.dumps(records,indent=2)+'\n');print('Reused prior25 control readings only after exact full-core identity; no fresh reading claim.')
