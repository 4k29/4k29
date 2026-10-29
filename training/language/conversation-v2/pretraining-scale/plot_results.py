"""Standalone numerical plots; CE/NLL are not language capability scores."""
import csv,collections
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
s=loader.load_checkpoint(P/'run/A/archive/checkpoint.json',read(P/'run/A/archive/checkpoint.json')['sha256']);traces={'A':s['trace']}
for a in ['B','C']:traces[a]=[e['trace']for e in map(json.loads,(P/'run'/a/'updates.jsonl').read_text().splitlines())if e['event']=='completed'and e['phase']=='retained']
fig,axes=plt.subplots(2,1,figsize=(9,7),layout='constrained')
for a,rows in traces.items():
 cumulative=0;data=[]
 for r in rows:cumulative+=r['targets'];data.append(dict(arm=a,step=r['step'],targets=cumulative,loss=r['loss'],gradient_norm_before_clip=r['gradient_norm_before_clip'],lr=r['lr']))
 with(P/(a+'-history.csv')).open('w')as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 xs=[];ys=[]
 for i in range(0,len(data),64):
  chunk=data[i:i+64];xs.append(chunk[-1]['targets']);ys.append(sum(r['loss']for r in chunk)/len(chunk))
 axes[0].plot(xs,ys,label=a+' TRAIN dropout (mean64)');axes[1].plot([r['targets']for r in data],[r['gradient_norm_before_clip']for r in data],label=a,alpha=.65)
 axes[1].axhline(1,color='black',linestyle=':',label='clip1');axes[0].set_ylabel('Causal CE');axes[1].set_ylabel('Preclip gradient L2')
for ax in axes:ax.set_xlabel('Retained teacher targets (per model)');ax.legend();ax.grid(alpha=.2)
fig.suptitle('Fixed initialization comparison and one clean data pass; not capability success');fig.savefig(P/'training-curves.png',dpi=160);plt.close(fig)
