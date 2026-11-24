"""Lossless full model/Adam/RNG/sampler checkpoints in Git-sized chunks."""
import hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent

def main():
 for arm in ['control','treatment']:
  source=H/'execution14'/(arm+'.pt');out=H/'execution14'/arm/'archive';out.mkdir(parents=True,exist_ok=True);whole=hashlib.sha256();rows=[];total=0
  with source.open('rb')as f:
   for i in range(100):
    b=f.read(32*1024**2)
    if not b:break
    p=out/('part-%03d.bin'%i);p.write_bytes(b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b).digest();rows.append({'path':p.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()});whole.update(b);total+=len(b)
  assert total==source.stat().st_size and whole.hexdigest()==hashlib.sha256(source.read_bytes()).hexdigest()
  (out/'checkpoint.json').write_text(json.dumps({'sha256':whole.hexdigest(),'bytes':total,'chunks':rows,'model':'own medium','inherited_updates':3470,'retained_new_updates':14,'final_optimizer_counter':3484,'active_schedule_cursor':14,'contains':'complete model/Adam/Torch and private RNG/legacy sampler provenance/active cursor/trace','formal_adoption':False},indent=2)+'\n');source.unlink()
 print('Both full checkpoints verified and archived in lossless <=32MiB chunks')
if __name__=='__main__':main()
