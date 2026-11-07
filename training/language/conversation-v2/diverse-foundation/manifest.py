"""Hash final public artifacts including checkpoint bytes obtainable from Git only."""
import pathlib,json,hashlib,subprocess
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3]
excluded={'MANIFEST.json','VERIFY.json','CI.json'}
def main():
 files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard',str(D.relative_to(ROOT))],cwd=ROOT,text=True).splitlines();records=[]
 for name in sorted(set(files)):
  p=ROOT/name
  if p.relative_to(D).as_posix()in excluded:continue
  raw=p.read_bytes()if p.exists()else subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)
  records.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
 result=dict(schema='public-evidence-sha256-v1',excludes=sorted(excluded),reason='manifest avoids its own hash; VERIFY/CI are subsequent verification receipts',records=records)
 (D/'MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n');print('Hashed',len(records),'public evidence files')
if __name__=='__main__':main()
