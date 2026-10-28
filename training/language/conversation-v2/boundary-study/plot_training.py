import csv,json,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import N

def main():
 fig,axes=plt.subplots(2,1,figsize=(10,7),layout='constrained')
 for name in ['control','boundary','clip5']:
  r=json.loads((N/'run'/name/'receipt.json').read_text());rows=r['retained_trace'];targets=[];total=0;loss=[]
  for i,x in enumerate(rows):
   total+=x['target_tokens'];targets.append(total);chunk=rows[max(0,i-63):i+1];loss.append(sum(z['loss']*z['target_tokens']for z in chunk)/sum(z['target_tokens']for z in chunk))
  with(N/(name+'-history.csv')).open('w')as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
  axes[0].plot(targets,loss,label=name+' TRAIN rolling64 (dropout on)');axes[1].plot(targets,[x['gradient_norm_before_clip']for x in rows],alpha=.6,linewidth=.7,label=name+' preclip norm');d=json.loads((N/'evaluation'/(name+'.json')).read_text());axes[0].scatter([379767],[d['prose_tf_nll']],label=name+' DEV terminal only')
 axes[1].axhline(1,color='black',linestyle='--',label='clip1');axes[1].axhline(5,color='gray',linestyle=':',label='clip5')
 for a in axes:a.grid(alpha=.2);a.legend(fontsize=8);a.set_xlabel('Actual retained targets')
 axes[0].set_ylabel('CE NLL, not language ability');axes[1].set_ylabel('Global L2 norm');fig.suptitle('Matched data allocation / one-factor clipping study');fig.savefig(N/'training-curves.png',dpi=150);plt.close(fig)
if __name__=='__main__':main()
