"""Freeze final artifacts only after full update and manual/parity audits."""
import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 audit=json.loads((ROOT/'optimizer-audit.json').read_text());comparison=json.loads((ROOT/'comparison.json').read_text())
 assert audit['actualAdditionalOptimizerUpdates']==10000 and audit['optimizerStepCounters']==[10000] and comparison['testStillUnopened']
 for name in ['RESULTS.md','performance.json','expanded-characters-10000/learning-curves.png','expanded-characters-10000/learning-curves.svg','expanded-characters-10000/learning-curves-source.json']:assert (ROOT/name).is_file(),name
 target=ROOT/'reproducibility-manifest.json';files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(ROOT.rglob('*')) if p.is_file() and p!=target and '__pycache__' not in p.parts and p.suffix!='.tmp']
 assert all(f['bytes']<100*1024*1024 for f in files)
 target.write_text(json.dumps(dict(files=files,previousInventoriesVerified=audit['previousInventoriesVerified'],python=sys.version,externalWeights=False,externalTokenizer=False,externalInferenceAPI=False,testStillUnopened=True,languageGatePassed=comparison['languageGatePassed'],naturalLanguageEstablished=comparison['naturalLanguageEstablished']),ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(files=len(files),actualAdditionalOptimizerUpdates=10000)))
if __name__=='__main__':main()
