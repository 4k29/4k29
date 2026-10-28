"""Export actual per-update loss/gradient history; validation never means generation success."""
import csv,json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=pathlib.Path(__file__).resolve().parent
def main():
 fig,axes=plt.subplots(2,1,figsize=(9,7),layout='constrained')
 for folder,label in [('run','LR 3e-5'),('lr-run','LR 1e-4')]:
  p=H/folder/'updates.jsonl'
  if not p.exists():continue
  rows=[r['trace']for r in map(json.loads,p.read_text().splitlines())if r['event']=='completed'and r['phase']=='retained'];targets=[];s=0;loss=[]
  for i,r in enumerate(rows):
   s+=r['target_tokens'];targets.append(s);recent=rows[max(0,i-127):i+1];loss.append(sum(x['loss']*x['target_tokens']for x in recent)/sum(x['target_tokens']for x in recent))
  with(H/(folder+'-history.csv')).open('w')as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
  axes[0].plot(targets,loss,label=label+' TRAIN, rolling128 weighted CE');axes[1].plot(targets,[r['gradient_norm_before_clip']for r in rows],linewidth=.6,alpha=.7,label=label+' preclip gradient norm')
 points=[(0,json.loads((H/'evaluation/initial.json').read_text())['prose_tf_nll'])]
 rows=json.loads((H/'run/foundation-trace.json').read_text())
 for p in(H/'validation').glob('*.json'):
  r=json.loads(p.read_text());points.append((sum(t['target_tokens']for t in rows[:r['cursor']]),r['DEV_nll']))
 p=H/'evaluation/foundation.json'
 if p.exists():points.append((sum(r['target_tokens']for r in rows),json.loads(p.read_text())['prose_tf_nll']))
 points.sort();axes[0].plot(*zip(*points),marker='o',label='LR3e-5 DEV (dropout off)');axes[0].set_ylabel('Token cross entropy');axes[0].legend();axes[0].set_title('One-pass Japanese foundation: numerical metrics, not language capability')
 axes[1].axhline(1,color='black',linestyle='--',label='Clip threshold1');axes[1].set_ylabel('Global L2 norm');axes[1].legend()
 for a in axes:a.set_xlabel('Actual retained TRAIN targets');a.grid(alpha=.2)
 fig.savefig(H/'training-curves.svg');fig.savefig(H/'training-curves.png',dpi=140);plt.close(fig)
 p=H/'training-curves.svg';p.write_text('\n'.join(line.rstrip()for line in p.read_text().splitlines())+'\n')
if __name__=='__main__':main()
