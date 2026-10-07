"""Export unsmoothed actual-update curves; likelihood is not fluency."""
import hashlib,json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    d=ROOT/'expanded-characters-10000';file=d/'metrics.json';m=json.loads(file.read_text());h=m['history']
    x=[r['step'] for r in h];assert x[-1]==10000
    fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
    for site in ['aozora','mic','env','jma','mdn']:
        axes[0].plot(x,[r['validation']['sites'][site]['nllPerUtf8Byte'] for r in h],marker='.',label=site)
    axes[0].plot(x,[r['validation']['nllPerUtf8Byte'] for r in h],color='black',marker='o',label='All canonical VAL')
    axes[0].set(ylabel='Held-out negative log likelihood / UTF-8 byte',xlabel='Saved optimizer update counter');axes[0].legend(fontsize=8)
    labels=['Expanded initial0','VAL-selected child']
    reviews=[json.loads((ROOT/name/'validation-review.json').read_text()) for name in ['initial-0','expanded-characters-10000']]
    for offset,key,total,label in [(-.18,'passed','total','All13 probes'),(.18,'corePassed','coreTotal','Original9 core')]:
        values=[v[key]/v[total] for v in reviews]
        bars=axes[1].bar([i+offset for i in range(2)],values,width=.36,label=label)
        for bar,v in zip(bars,reviews):axes[1].text(bar.get_x()+bar.get_width()/2,bar.get_height()+.015,f"{v[key]}/{v[total]}",ha='center',fontsize=8)
    axes[1].axhline(.8,color='gray',linestyle='--',label='Requirement applies separately per genre')
    axes[1].set(ylabel='First-sentence success on development probes',ylim=(0,1),xlabel='Same8-layer model / 192 new tokens',xticks=[0,1],xticklabels=labels);axes[1].legend(fontsize=7)
    fig.suptitle('Own expanded character model: likelihood and development quality',fontsize=12)
    fig.savefig(d/'learning-curves.png',dpi=150);fig.savefig(d/'learning-curves.svg');plt.close(fig)
    (d/'learning-curves-source.json').write_text(json.dumps(dict(metricsSha256=hashlib.sha256(file.read_bytes()).hexdigest(),savedOptimizerSteps=x,smoothing=False,discardedUpdatesExcluded=True,recoveryRecordSha256=hashlib.sha256((ROOT/'recovery.json').read_bytes()).hexdigest(),testUsed=False,warning='Likelihood is not fluency. Manual development first-sentence scores do not certify full-output coherence; final gate also requires each genre in both expanded13 and original9 plus full-output non-looping.'),indent=2)+'\n')
if __name__=='__main__':main()
