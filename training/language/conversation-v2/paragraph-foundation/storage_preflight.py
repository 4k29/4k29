"""Verify original full-state bytes and durable two-generation atomic-save budget; zero updates."""
import pathlib,json,hashlib,subprocess,os,shutil,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3]
manifest=ROOT/'training/language/conversation-v2/modern-corpus/next-foundation/artifacts/B-6361/checkpoint.json'
m=json.loads(manifest.read_text());scratch=P/'private/source-B-6361.pt';scratch.parent.mkdir(exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
if not scratch.exists():
 with scratch.open('wb')as out:
  for chunk in m['chunks']:
   rel=str((manifest.parent/chunk['path']).relative_to(ROOT));part=subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT)
   assert len(part)==chunk['bytes']and hashlib.sha256(part).hexdigest()==chunk['sha256'];out.write(part)
assert scratch.stat().st_size==m['bytes']and sha(scratch)==m['sha256']
durable=pathlib.Path('/workspace/4k29/training/language/conversation-v2/paragraph-foundation/private/storage-probe');durable.mkdir(parents=True,exist_ok=True)
before=shutil.disk_usage(durable).free;reserve=256*1024**2
assert before>=2*m['bytes']+reserve,('insufficient atomic-save capacity',before)
minimum=before
for i in range(2):
 pending=durable/'checkpoint.pending'
 with scratch.open('rb')as src,pending.open('wb')as out:
  shutil.copyfileobj(src,out);out.flush();os.fsync(out.fileno())
 minimum=min(minimum,shutil.disk_usage(durable).free);assert minimum>=reserve
 assert sha(pending)==m['sha256'];os.replace(pending,durable/'checkpoint.pt');fd=os.open(durable,os.O_RDONLY);os.fsync(fd);os.close(fd)
assert sha(durable/'checkpoint.pt')==m['sha256']
(durable/'checkpoint.pt').unlink();durable.rmdir()
r=dict(source_sha256=m['sha256'],checkpoint_bytes=m['bytes'],source_restored_from_committed_chunks=True,atomic_replacement_generations=2,free_before=before,minimum_observed_free=minimum,reserve_bytes=reserve,full_state_tensor_restore='pending independent numerical audit',optimizer_updates=0,tmpfs_not_durable=True,durable_probe_removed=True)
(P/'STORAGE_PREFLIGHT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
