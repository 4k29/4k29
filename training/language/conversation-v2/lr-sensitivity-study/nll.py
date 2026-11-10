"""Same exposed LF1 input windows and nonLF body targets for all three models."""
from mix_runtime import *
import argparse,collections
sys.path.insert(0,str(V));from core import decoder
@torch.inference_mode()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--checkpoint',required=True);ap.add_argument('--name',required=True);a=ap.parse_args();out=P/'NLL';out.mkdir(exist_ok=True);dest=out/(a.name+'.json');assert not dest.exists();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);st=torch.load(a.checkpoint,map_location='cpu',weights_only=False)['trajectory']
 with torch.random.fork_rng():m=decoder(st['config']);m.load_state_dict(st['model']);m.eval()
 dev=json.load(gzip.open(P/'DEV_BODY_NLL.json.gz','rt'));tot=collections.defaultdict(lambda:[0.,0]);alltot=collections.defaultdict(lambda:[0.,0]);details=[];calls=0;begun=time.monotonic()
 for i in range(0,len(dev),4):
  batch=dev[i:i+4];x,y=pack(batch);v=m(x);calls+=1
  for j,r in enumerate(batch):
   n=len(r['tokens'])-1;mask=torch.tensor(r['body_mask']);loss=torch.nn.functional.cross_entropy(v[j,:n],y[j,:n],reduction='none');s=float(loss[mask].sum());count=int(mask.sum());tot[r['source']][0]+=s;tot[r['source']][1]+=count;alltot[r['source']][0]+=float(loss.sum());alltot[r['source']][1]+=n;details.append(dict(id=r['id'],source=r['source'],body_NLL_sum=s,body_targets=count,total_NLL_sum=float(loss.sum()),total_targets=n))
 write(dest,dict(name=a.name,checkpoint_sha256=sha(a.checkpoint),groups={k:dict(NLL=s/n,targets=n) for k,(s,n) in tot.items()},all_valid_token_groups={k:dict(NLL=s/n,targets=n) for k,(s,n) in alltot.items()},windows=details,body_definition='IDs>5 except LF16; exclude BOS/EOS/role/PAD and LF from loss metric only, never inference vocabulary',exposure='Developed/exposed DEV, not sealed TEST; ENV separately uses exposed TRAIN boundary TF, no independent ENV DEV exists here',model_forwards=calls,optimizer_calls=0,seconds=time.monotonic()-begun));print(a.name,read(dest)['groups'],flush=True)
if __name__=='__main__':main()
