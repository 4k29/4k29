"""Read a completed atomic snapshot once; add descriptive validation, never select it."""
import gzip,hashlib,io,json
from runtime import H,torch,pack,restore_isolated
def main():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);raw=(H/'run/foundation.pt').read_bytes();s=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=False);model,_,_=restore_isolated(s['trajectory']);model.eval();d=json.load(gzip.open(H/'schedule.json.gz','rt'));total=targets=0
 with torch.no_grad():
  for i in range(0,len(d['dev']),4):
   x,y=pack(d['dev'][i:i+4]);loss=torch.nn.functional.cross_entropy(model(x).reshape(-1,3997),y.reshape(-1),ignore_index=-100,reduction='sum');total+=float(loss);targets+=int(y.ne(-100).sum())
 out=H/'validation';out.mkdir(exist_ok=True);r=dict(cursor=s['active_cursor'],checkpoint_sha256=hashlib.sha256(raw).hexdigest(),DEV_nll=total/targets,targets=targets,optimizer_updates=0,scope='descriptive periodic validation only; terminal selection remains fixed, no generation inspected');(out/(str(s['active_cursor'])+'.json')).write_text(json.dumps(r,indent=2)+'\n');print(r)
if __name__=='__main__':main()
