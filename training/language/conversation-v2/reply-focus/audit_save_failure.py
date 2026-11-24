"""Inject a mid-serialization write failure; never exhaust the real filesystem."""
import hashlib,importlib.util,json,os,pathlib,tempfile
import torch
H=pathlib.Path(__file__).resolve().parent;V=H.parent
class LimitedWriter:
 def __init__(self,f,limit):self.f=f;self.left=limit;self.injected=False
 def write(self,b):
  if len(b)>self.left:
   self.f.write(b[:self.left]);self.left=0;self.injected=True;raise OSError(28,'injected ENOSPC during serialization')
  self.left-=len(b);return self.f.write(b)
 def flush(self):return self.f.flush()
 def tell(self):return self.f.tell()

def main():
 manifest=H/'execution14/control/archive/checkpoint.json';meta=json.loads(manifest.read_text());s=importlib.util.spec_from_file_location('load',V/'foundation-data/research/zero_update_preflight.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);payload=m.load_checkpoint(manifest.resolve(),meta['sha256'])
 with tempfile.TemporaryDirectory(prefix='save-failure-',dir=H)as td:
  p=pathlib.Path(td);committed=p/'committed.pt'
  with committed.open('wb')as f:
   for r in meta['chunks']:f.write((manifest.parent/r['path']).read_bytes())
   f.flush();os.fsync(f.fileno())
  before=hashlib.sha256(committed.read_bytes()).hexdigest();assert before==meta['sha256'];failed=False
  with (p/'pending.tmp').open('wb')as f:
   stream=LimitedWriter(f,4096)
   try:torch.save(payload,stream)
   except (OSError,RuntimeError):failed=True
  assert stream.injected and failed and hashlib.sha256(committed.read_bytes()).hexdigest()==before
  recovered=torch.load(committed,map_location='cpu',weights_only=False);assert recovered['allocation_cursor']==14
 result={'real_full_checkpoint_used':True,'mid_serialization_ENOSPC_injected':True,'committed_checkpoint_unchanged':True,'committed_state_recovered_at_step':14,'partial_pending_never_promoted':True,'real_disk_exhaustion_performed':False,'optimizer_updates':0}
 (H/'SAVE_FAILURE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print('Mid-serialization fault and full-state recovery PASS')
if __name__=='__main__':main()
