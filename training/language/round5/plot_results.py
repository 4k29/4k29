"""Export unsmoothed actual-update curves; likelihood is not fluency."""
import hashlib,json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    d=ROOT/'characters-10000';file=d/'metrics.json';m=json.loads(file.read_text());h=m['history']
    x=[r['step'] for r in h];assert x[-1]==10000
    fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
    for site in ['aozora','mic','env','jma']:
        axes[0].plot(x,[r['validation']['sites'][site]['nllPerUtf8Byte'] for r in h],marker='.',label=site)
    axes[0].plot(x,[r['validation']['nllPerUtf8Byte'] for r in h],color='black',marker='o',label='All canonical VAL')
    axes[0].set(ylabel='Held-out negative log likelihood / UTF-8 byte',xlabel='Actual optimizer updates');axes[0].legend(fontsize=8)
    for name,label in [('baseline-1000','Saved 1,000'),('characters-10000','VAL-selected')]:
        v=json.loads((ROOT/name/'validation-review.json').read_text())
        axes[1].bar(label,v['passed']/v['total'],label=f"{label}: {v['passed']}/{v['total']}")
    axes[1].axhline(.8,color='gray',linestyle='--',label='Per-group first-sentence requirement')
    axes[1].set(ylabel='First-sentence success on development probes',ylim=(0,1),xlabel='Same character model / 192 new tokens');axes[1].legend(fontsize=7)
    fig.suptitle('Own character Transformer: likelihood and manual development quality',fontsize=12)
    fig.savefig(d/'learning-curves.png',dpi=150);fig.savefig(d/'learning-curves.svg');plt.close(fig)
    (d/'learning-curves-source.json').write_text(json.dumps(dict(metricsSha256=hashlib.sha256(file.read_bytes()).hexdigest(),actualSteps=x,smoothing=False,testUsed=False,warning='Likelihood is not fluency. Manual development first-sentence scores do not certify full-output coherence; final gate also requires each genre and full-output non-looping.'),indent=2)+'\n')
if __name__=='__main__':main()
