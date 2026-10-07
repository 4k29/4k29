"""Plot exact recorded canonical validation values, not language success."""
import hashlib,json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    path=ROOT/'raw-chains-10000/metrics.json';m=read(path);h=m['history'];choice=read(ROOT/'vocabulary-choice.json')
    assert (ROOT/'raw-chains-10000/result.json').exists() and h[-1]['step']==10000
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','svg.hashsalt':'4k29-own-raw-round3','axes.spines.top':False,'axes.spines.right':False})
    fig,(ax,b)=plt.subplots(1,2,figsize=(11,4.8),gridspec_kw={'width_ratios':[3,1.2]})
    x=[r['step'] for r in h]
    colors={'aozora':'#0f766e','mic':'#2563eb','env':'#16a34a','jma':'#d97706'}
    for site,color in colors.items():ax.plot(x,[r['validation']['sites'][site]['nllPerUtf8Byte'] for r in h],color=color,linewidth=1.2,label=site.upper())
    ax.plot(x,[r['validation']['nllPerUtf8Byte'] for r in h],color='#111827',linewidth=2.4,label='All canonical held chains')
    ax.set(xlabel='Completed optimizer updates in new eight-layer run',ylabel='Validation NLL / UTF-8 byte (nats)',xlim=(0,10000));ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8,frameon=False)
    rows=choice['runs'];values=[r['validationNllPerUtf8Byte'] for r in rows];bars=b.bar([str(r['merges']) for r in rows],values,color=['#94a3b8','#2563eb']);b.bar_label(bars,labels=[f'{v:.3f}' for v in values],padding=4)
    b.set(xlabel='Own BPE merge rules',ylabel='Validation NLL / byte',ylim=(0,1.8),title='1,000-update pilots');b.grid(axis='y',alpha=.2);b.set_axisbelow(True)
    fig.suptitle('Own raw Japanese: original short quotations and connected prose',fontsize=12)
    fig.text(.015,.018,'No smoothing. Pilots differ in parameters and byte exposure. Likelihood does not establish natural or meaningful generation.',fontsize=8,color='#475569');fig.tight_layout(rect=(0,.06,1,.96))
    out=path.parent;svg=out/'learning-curves.svg';fig.savefig(svg,metadata={'Date':None});svg.write_text('\n'.join(s.rstrip() for s in svg.read_text().splitlines())+'\n');fig.savefig(out/'learning-curves.png',dpi=180);plt.close(fig)
    (out/'figure-sources.json').write_text(json.dumps(dict(metricsSha256=sha(path),vocabularyChoiceSha256=sha(ROOT/'vocabulary-choice.json'),lastRecordedUpdate=h[-1]['step'],testUsed=False,unit='Canonical exact original paragraph chains',note='Raw next-token likelihood only, not a Japanese fluency or QA score. Surviving1000 checkpoint resumed after environment restart; unknown unsaved updates are not counted.'),indent=2)+'\n')
if __name__=='__main__':main()
