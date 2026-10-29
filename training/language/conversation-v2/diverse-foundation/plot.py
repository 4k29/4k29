from common import *
import csv,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(11,4))
for arm in ['A','B']:
 p=D/'run'/arm/'updates.jsonl';done=[json.loads(l)['trace']for l in p.read_text().splitlines()if json.loads(l)['event']=='completed'and json.loads(l)['phase']=='retained'];keys=['step','targets','loss','gradient_norm_before_clip','lr','EOS_targets','role_targets'];total=0;records=[]
 for r in done:total+=r['targets'];records.append(dict(**r,cumulative_targets=total))
 with(D/(arm+'-history.csv')).open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=keys+['cumulative_targets']);w.writeheader();w.writerows(records)
 smoothed=[statistics.mean(r['loss']for r in records[max(0,i-63):i+1])for i in range(len(records))];axes[0].plot([r['cumulative_targets']/1e6 for r in records],smoothed,label=arm);axes[1].plot([r['cumulative_targets']/1e6 for r in records],[r['gradient_norm_before_clip']for r in records],alpha=.35,label=arm)
axes[0].set(xlabel='Additional teacher targets (millions)',ylabel='TRAIN CE (last64 updates mean)');axes[1].set(xlabel='Additional teacher targets (millions)',ylabel='Global gradient norm before clip');axes[1].axhline(1,color='black',linestyle='--',linewidth=.7)
for a in axes:a.legend();a.grid(alpha=.2)
fig.tight_layout();fig.savefig(D/'training-curves.png',dpi=160);plt.close(fig)
