from pathlib import Path
import json,hashlib,subprocess,shutil
repo=Path('/workspace/4k29');B=repo/'training/language';R=B/'round47';E=R/'execution';manifest=json.loads((R/'source-manifest.json').read_text());protected={(R/x['path']).resolve()for x in manifest['files']};before=Path(subprocess.check_output(['git','rev-parse','--git-path','info/sparse-checkout'],cwd=repo,text=True).strip());before=repo/before if not before.is_absolute()else before;patterns=before.read_text();rows=[];to_omit=[]
for n in [40,41]:
 for m in (B/f'round{n}').rglob('*.pt.chunks.json'):
  d=json.loads(m.read_text());h=hashlib.sha256();size=0
  for c in d['chunks']:
   p=m.parent/c['path'];assert p.resolve()not in protected and p.is_file();b=p.read_bytes();assert len(b)==c['bytes']and hashlib.sha256(b).hexdigest()==c['sha256'];h.update(b);size+=len(b);rel=str(p.relative_to(repo));oid=subprocess.check_output(['git','ls-files','-s','--',rel],cwd=repo,text=True).split()[1];assert subprocess.check_output(['git','hash-object',str(p)],cwd=repo,text=True).strip()==oid;rows.append(dict(path=rel,bytes=len(b),sha256=c['sha256'],gitBlob=oid));to_omit.append('!/'+rel)
  assert h.hexdigest()==d['sha256']and size==d['bytes']
assert len(rows)>=20
(E/'sparse-checkout-before.txt').write_text(patterns);updated=patterns.rstrip()+'\n'+'\n'.join(to_omit)+'\n';oldfree=shutil.disk_usage(repo).free
subprocess.run(['git','sparse-checkout','set','--no-cone','--stdin'],cwd=repo,input=updated,text=True,check=True)
for row in rows:assert not(repo/row['path']).exists();subprocess.run(['git','ls-files','--error-unmatch',row['path']],cwd=repo,check=True,stdout=subprocess.DEVNULL)
proof=dict(actualR47OptimizerUpdates=0,onlyArchivedWorkingTreeCopiesOmitted=True,gitBlobsAndHistoryUnchanged=True,allPartsAndConcatenatedCheckpointShasVerifiedBeforeOmission=True,noFrozenInputOmitted=True,rawArchivedCheckpointPartsOmitted=len(rows),omittedFileBytes=sum(r['bytes']for r in rows),freeBytesBefore=oldfree,freeBytesAfter=shutil.disk_usage(repo).free,concurrentPackingMayAffectObservedFreeDelta=True,restore='Remove only the listed !/path patterns from sparse-checkout and run git sparse-checkout set --no-cone --stdin with remaining patterns; Git materializes original byte-identical blobs',files=rows)
(E/'archived-checkpoint-sparse-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items()if k!='files'}))
p=R/'WORKSPACE_STORAGE.md';p.write_text(p.read_text()+'\nR47のarchived-checkpoint-sparse-proof.jsonにあるR40/R41分割ファイルの作業ツリーコピーだけを省略した。全Git blob/履歴は保持し、各partとconcat SHAを事前確認。新入力は除外。復元時は対象の!/path行だけをsparse patternから除いてset --no-cone --stdinを適用し、十分な空き容量を確認する。\n')
