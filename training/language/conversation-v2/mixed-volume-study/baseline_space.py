"""Only missing baseline P(space) on40 exact histories; prior full evaluations reused."""
from mix_runtime import *
import argparse
sys.path.insert(0,str(V));from core import decoder
@torch.inference_mode()
def main():
 torch.set_num_threads(2);obj=torch.load(SCRATCH/'initial.pt',map_location='cpu',weights_only=False);st=obj['trajectory']
 with torch.random.fork_rng():m=decoder(st['config']);m.load_state_dict(st['model']);m.eval()
 base=read(V/'mixed-retention-study/evaluation/terminal-MIX-boundaries.json');out=[]
 for c in base['cases']:
  pref=c['inputs']['C'];tail=c['tail'];v=m(torch.tensor([pref+tail[:7]]))[0,len(pref)-1];lp=v.double().log_softmax(-1);out.append(dict(id=c['id'],P_space=float(lp[38].exp()),space_rank=1+int((v>v[38]).sum()),argmax=int(v.argmax())))
 write(P/'BASELINE_SPACE.json',dict(source_sha256=sha(SCRATCH/'initial.pt'),cases=out,model_forwards=40,optimizer_calls=0,scope='Only previously absent P(space); same original TF-shaped prefix and full vocabulary; baseline generation/NLL-body reused separately'))
if __name__=='__main__':main()
