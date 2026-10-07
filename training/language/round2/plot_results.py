"""Source-backed standalone curves; likelihood is not a fluency score."""
import hashlib,json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    metric=ROOT/'raw-modern-million/metrics.json';data=read(metric);h=data['history'];choice=read(ROOT/'vocabulary-choice.json');plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','svg.hashsalt':'4k29-own-raw-round2','axes.spines.top':False,'axes.spines.right':False})
    fig,(ax,b)=plt.subplots(1,2,figsize=(11,4.8),gridspec_kw={'width_ratios':[3,1.2]});x=[r['step'] for r in h]
    colors={'aozora':'#0f766e','mic':'#2563eb','env':'#16a34a','mdn':'#7c3aed','jma':'#d97706','maff':'#db2777'}
    for site,color in colors.items():ax.plot(x,[r['validation']['sites'][site]['nllPerUtf8Byte'] for r in h],color=color,linewidth=1.2,label=site.upper())
    ax.plot(x,[r['validation']['nllPerUtf8Byte'] for r in h],color='#111827',linewidth=2.4,label='All canonical held paragraphs')
    child_metric=ROOT/'prefix-million/metrics.json';child=None
    if (child_metric.parent/'result.json').exists():
        child=read(child_metric);offset=child['settings']['parentSelectedSteps'];cx=[offset+r['step'] for r in child['history']]
        for site,color in colors.items():ax.plot(cx,[r['validation']['sites'][site]['nllPerUtf8Byte'] for r in child['history']],color=color,linewidth=1.2,linestyle='--')
        ax.plot(cx,[r['validation']['nllPerUtf8Byte'] for r in child['history']],color='#111827',linewidth=2.4,linestyle='--',label='Prefix-view continuation');ax.axvline(offset,color='#64748b',linewidth=.7,alpha=.5)
    xmax=(child['settings']['parentSelectedSteps']+child['settings']['steps']) if child else data['settings']['steps']
    ax.set(xlabel='Completed optimizer updates in six-layer weight lineage',ylabel='Validation NLL / UTF-8 byte (nats)',xlim=(0,xmax));ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8,frameon=False)
    rows=choice['runs'];values=[r['validationNllPerUtf8Byte'] for r in rows];bars=b.bar([str(r['merges']) for r in rows],values,color=['#94a3b8','#2563eb']);b.bar_label(bars,labels=[f'{v:.3f}' for v in values],padding=4);b.set(xlabel='Own BPE merge rules',ylabel='Validation NLL / byte',ylim=(0,1.8),title='1,000-update pilots');b.grid(axis='y',alpha=.2);b.set_axisbelow(True)
    fig.suptitle('Own raw Japanese: modern prose, fresh vocabulary and six decoder layers',fontsize=12);fig.text(.015,.018,'No smoothing. Vocabulary pilots differ in parameter count and byte exposure. Likelihood alone does not prove natural or meaningful generation.',fontsize=8,color='#475569');fig.tight_layout(rect=(0,.06,1,.96))
    out=metric.parent;svg=out/'learning-curves.svg';fig.savefig(svg,metadata={'Date':None});svg.write_text('\n'.join(s.rstrip() for s in svg.read_text().splitlines())+'\n');fig.savefig(out/'learning-curves.png',dpi=180);plt.close(fig)
    (out/'figure-sources.json').write_text(json.dumps(dict(metricsSha256=sha(metric),prefixMetricsSha256=sha(child_metric) if child else None,vocabularyChoiceSha256=sha(ROOT/'vocabulary-choice.json'),lastRecordedUpdate=h[-1]['step'],prefixLastRecordedUpdate=child['history'][-1]['step'] if child else None,testUsed=False,unit='Canonical complete original paragraphs',note='Raw next-token validation only. Not a Japanese fluency/owner-QA score. Dashed continuation resets optimizer/RNG, retains its own parent weights, and changes TRAIN representations.'),indent=2)+'\n')
if __name__=='__main__':main()
