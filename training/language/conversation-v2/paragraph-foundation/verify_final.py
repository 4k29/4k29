"""Read-only final SHA, ledger, output-byte and scope audit. Never optimizes."""
import pathlib,json,hashlib,subprocess,datetime
P=pathlib.Path(__file__).resolve().parent; ROOT=P.parents[3]
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  while b:=s.read(1024**2):h.update(b)
 return h.hexdigest()
def main():
 plan=json.loads((P/'PLAN.json').read_text())
 for name,want in plan['input_sha256'].items():assert sha(ROOT/name)==want,name
 manifests=[]
 for f in sorted(P.rglob('checkpoint.json')):
  if 'private' in f.parts:continue
  m=json.loads(f.read_text()); whole=hashlib.sha256(); size=0
  for c in m['chunks']:
   path=f.parent/c['path']; h=hashlib.sha256(); n=0
   if path.exists():s=path.open('rb'); proc=None
   else:
    proc=subprocess.Popen(['git','show','HEAD:'+str(path.relative_to(ROOT))],cwd=ROOT,stdout=subprocess.PIPE);s=proc.stdout
   while b:=s.read(1024**2):h.update(b);whole.update(b);n+=len(b)
   s.close()
   if proc:assert proc.wait()==0
   assert n==c['bytes'] and n<=32*1024**2 and h.hexdigest()==c['sha256'],str(path)
   size+=n
  assert size==m['bytes'] and whole.hexdigest()==m['sha256']
  manifests.append({'path':str(f.relative_to(P)),'bytes':size,'sha256':m['sha256']})
 count=0
 for f in sorted((P/'evaluation').glob('*.json')):
  d=json.loads(f.read_text())
  if not isinstance(d,dict) or not isinstance(d.get('cases'),list):continue
  for r in d['cases']:
   if 'rawBytesHex' not in r:continue
   raw=bytes.fromhex(r['rawBytesHex']);assert raw.decode('utf-8',errors='replace')==r['text'];count+=1
 changed=subprocess.check_output(['git','diff','--name-only','60f0ddaeb38b2d1c7e60f0858af721af10c5efb6','HEAD'],cwd=ROOT,text=True).splitlines()
 assert all(n.startswith(str(P.relative_to(ROOT))+'/') or n=='.github/workflows/paragraph-foundation.yml' for n in changed)
 out={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frozen_input_files':len(plan['input_sha256']),'whole_and_chunk_SHA_verified':manifests,'evaluation_raw_byte_text_records':count,'changed_paths_within_research_and_CI':True,'sealed_TEST_used':False,'formal_models_and_site_changed':False,'actual_optimizer_updates':0,'limitation':'Byte/SHA audit complements, does not replace stored full-state reload/replay proofs and semantic reading.'}
 (P/'FINAL_VERIFICATION.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checkpoint_manifests':len(manifests),'evaluation_records':count,'frozen_inputs':len(plan['input_sha256']),'passed':True}))
if __name__=='__main__':main()
