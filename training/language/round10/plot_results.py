"""Standalone figures from audited saved validation points and raw manual scores."""
import hashlib,json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 choice=read(ROOT/'vocabulary-choice.json');main=ROOT/f"word-{choice['wordMerges']}-continue-10000";comparison=read(ROOT/'comparison.json');audit=read(ROOT/'optimizer-audit.json');metrics=read(main/'metrics.json')
 data=dict(pilots=[],main=dict(savedOptimizerSteps=[r['step'] for r in metrics['history']],nllPerUtf8Byte=[r['validation']['nllPerUtf8Byte'] for r in metrics['history']],metricsSha256=sha(main/'metrics.json')),manualComparisonSha256=sha(ROOT/'comparison.json'),completedUpdates=12000,selectedWeightLineageUpdates=audit['selectedWeightLineageUpdates'],note='Distinct pilot branches and main updates have separate axes. Only saved canonical full-VAL points; no invented interpolation measurements. Main0 is an already trained selected pilot warm start.')
 fig,axes=plt.subplots(1,3,figsize=(15,4.8),layout='constrained')
 for n in [512,1024]:
  folder=ROOT/f'word-{n}-pilot-1000';m=read(folder/'metrics.json');p=dict(wordRules=n,savedOptimizerSteps=[r['step'] for r in m['history']],nllPerUtf8Byte=[r['validation']['nllPerUtf8Byte'] for r in m['history']],metricsSha256=sha(folder/'metrics.json'));data['pilots'].append(p);axes[0].plot(p['savedOptimizerSteps'],p['nllPerUtf8Byte'],'o-',label=f'{n} word rules')
 axes[0].set(title='Separate pilot branches',xlabel='Saved pilot optimizer update',ylabel='Canonical VAL NLL / UTF8 byte');axes[0].legend();axes[0].grid(alpha=.2)
 axes[1].plot(data['main']['savedOptimizerSteps'],data['main']['nllPerUtf8Byte'],'o-',color='#2563eb');axes[1].set(title=f"Main: {choice['wordMerges']} word rules",xlabel='Saved main optimizer update',ylabel='Canonical VAL NLL / UTF8 byte');axes[1].grid(alpha=.2)
 names=['main-initial-0',main.name];categories=['First sentence','Nonloop','Full meaning'];source=[]
 for i,name in enumerate(names):
  r=comparison['runs'][name];values=[r['passed'],r['fullOutputNonLoop'],r['fullOutputMeaningful']];source.append(dict(run=name,values=values,total=r['total']));axes[2].bar([x+(i-.5)*.34 for x in range(3)],values,width=.34,label='Main0' if i==0 else 'Selected main')
 axes[2].set(title='Unedited VAL continuations',xticks=range(3),xticklabels=categories,ylabel='Outputs passing criterion',ylim=(0,17.8));axes[2].legend();axes[2].grid(axis='y',alpha=.2);data['scores']=source
 fig.suptitle('Own raw Japanese word BPE — likelihood and language are separate measures',fontsize=14)
 fig.savefig(ROOT/'learning-curves.png',dpi=160);fig.savefig(ROOT/'learning-curves.svg');plt.close(fig)
 (ROOT/'learning-curves-source.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
