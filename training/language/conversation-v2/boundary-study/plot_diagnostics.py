import csv,json,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import N

def main():
 names=['initial','foundation','foundation-mixed','foundation-lr'];metrics=['p_EOS','p_whitespace','p_contains_ASCII_digit','p_previous16_tokens'];fig,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained');csvrows=[]
 for name in names:
  cases=json.loads((N/'diagnostic'/(name+'.json')).read_text())['cases']
  for j in range(128):
   rows=[r['steps'][j]for r in cases if len(r['steps'])>j]
   if not rows:continue
   row=dict(model=name,position=j,active_generations=len(rows),**{m:statistics.mean(r[m]for r in rows)for m in metrics});csvrows.append(row)
  for ax,m in zip(axes.flat,metrics):
   rs=[r for r in csvrows if r['model']==name];ax.plot([r['position']for r in rs],[r[m]for r in rs],label=name);ax.set_title(m);ax.set_xlabel('Generated token position');ax.set_ylabel('Mean probability mass, active sequences only');ax.set_ylim(0,1);ax.grid(alpha=.2)
 axes[0,0].legend();fig.suptitle('Saved fixed greedy histories: token-spelling proxies; early EOS censors later positions');fig.savefig(N/'probability-trajectories.png',dpi=150);plt.close(fig)
 with(N/'probability-trajectories.csv').open('w')as f:
  w=csv.DictWriter(f,fieldnames=list(csvrows[0]),lineterminator='\n');w.writeheader();w.writerows(csvrows)
if __name__=='__main__':main()
