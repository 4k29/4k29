"""Plot actual likelihood and development scores without claiming fluency."""
import hashlib,json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def main():
    path=ROOT/'boundary-focus-2000/metrics.json';data=read(path);h=data['history'];assert h[-1]['step']==2000
    parent=read(ROOT.parent/'round3/raw-chains-10000/validation-review.json');child=read(ROOT/'boundary-focus-2000/validation-review.json')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','svg.hashsalt':'4k29-own-raw-round4','axes.spines.top':False,'axes.spines.right':False})
    fig,(ax,b)=plt.subplots(1,2,figsize=(11,4.8));x=[r['step'] for r in h]
    ax.plot(x,[r['validation']['nllPerUtf8Byte'] for r in h],color='#2563eb',marker='o',label='Canonical full chains')
    ax.axhline(h[0]['validation']['nllPerUtf8Byte'],color='#64748b',linestyle='--',label='Own parent');ax.set(xlabel='Actual additional optimizer updates',ylabel='Validation NLL / UTF-8 byte (nats)',xticks=x);ax.grid(axis='y',alpha=.2);ax.legend(frameon=False)
    groups=['First sentence passes','Non-loop full outputs','Valid token outputs'];before=[parent['passed'],sum(g['fullOutputNonLoop'] for g in parent['groups'].values()),parent['validTokenOutputs']];after=[child['passed'],sum(g['fullOutputNonLoop'] for g in child['groups'].values()),child['validTokenOutputs']]
    positions=list(range(3));b.bar([v-.18 for v in positions],before,width=.36,color='#94a3b8',label='Own parent');b.bar([v+.18 for v in positions],after,width=.36,color='#2563eb',label='Boundary-focused');b.set(xticks=positions,xticklabels=groups,ylim=(0,9.7),ylabel='Development continuations / 9');b.tick_params(axis='x',labelsize=8);b.grid(axis='y',alpha=.2);b.set_axisbelow(True);b.legend(frameon=False)
    fig.suptitle('Own raw continuation: a marginal first-sentence gain, stability still fails',fontsize=12);fig.text(.02,.025,'No smoothing. Same development probes. Assistant scoring, not blind human evaluation. Fresh TEST remains unopened.',fontsize=8,color='#475569');fig.tight_layout(rect=(0,.07,1,.94))
    out=path.parent;svg=out/'learning-curves.svg';fig.savefig(svg,metadata={'Date':None});svg.write_text('\n'.join(s.rstrip() for s in svg.read_text().splitlines())+'\n');fig.savefig(out/'learning-curves.png',dpi=180);plt.close(fig)
    (out/'figure-sources.json').write_text(json.dumps(dict(metricsSha256=hashlib.sha256(path.read_bytes()).hexdigest(),parentReviewSha256=hashlib.sha256((ROOT.parent/'round3/raw-chains-10000/validation-review.json').read_bytes()).hexdigest(),childReviewSha256=hashlib.sha256((out/'validation-review.json').read_bytes()).hexdigest(),lastRecordedAdditionalUpdates=2000,testUsed=False,note='Likelihood and assistant development counts; not production response quality or speed.'),indent=2)+'\n')
if __name__=='__main__':main()
