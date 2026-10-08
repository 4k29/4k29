"""Freeze completed artifacts only after raw/parity/manual/optimizer review."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent

def main():
 audit=json.loads((ROOT/'optimizer-audit.json').read_text());assert audit['actualCompletedUpdatesThisRound']==12000 and audit['actualCompletedMainUpdates']==10000
 comparison=json.loads((ROOT/'comparison.json').read_text());assert comparison['testStillUnopened']
 for name in ['RESULTS.md','performance.json','learning-curves.png','learning-curves.svg','learning-curves-source.json']:assert (ROOT/name).is_file(),name
 target=ROOT/'reproducibility-manifest.json';files=[]
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file() or p==target or '__pycache__' in p.parts or p.suffix=='.tmp':continue
  assert p.stat().st_size<100*1024*1024,p
  files.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 target.write_text(json.dumps(dict(files=files,completedUpdatesThisRound=12000,naturalLanguageEstablished=comparison['naturalLanguageEstablished'],testStillUnopened=True,publicModelReplaced=False,externalWeights=False,externalTokenizer=False,externalInferenceAPI=False),indent=2)+'\n')
 print(json.dumps(dict(frozenFiles=len(files),completedUpdatesThisRound=12000)))
if __name__=='__main__':main()
