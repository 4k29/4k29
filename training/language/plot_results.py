"""Standalone source-backed likelihood figures; never a fluency/knowledge score."""
import hashlib,json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parent

def save_svg(fig,path):
 fig.savefig(path,metadata={'Date':None})
 # Matplotlib emits trailing spaces in SVG path lines; preserve visual data.
 path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')

def main():
 metrics=ROOT/'raw-million'/'metrics.json';data=json.loads(metrics.read_text());history=data['history'];choice=json.loads((ROOT/'vocabulary-choice.json').read_text())
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','svg.hashsalt':'4k29-own-raw-japanese'})
 fig,(left,right)=plt.subplots(1,2,figsize=(11,4.4),gridspec_kw={'width_ratios':[3,1.2]})
 colors={'aozora':'#0f766e','mdn':'#2563eb','jma':'#d97706','maff':'#9333ea'};labels={'aozora':'Aozora: literature','mdn':'MDN: web explanations','jma':'JMA: weather','maff':'MAFF: explanations'}
 x=[r['step'] for r in history]
 for site in ['aozora','mdn','jma','maff']:left.plot(x,[r['validation']['sites'][site]['nllPerUtf8Byte'] for r in history],color=colors[site],linewidth=1.5,label=labels[site])
 left.plot(x,[r['validation']['nllPerUtf8Byte'] for r in history],color='#111827',linewidth=2.5,label='All held validation documents');left.set(xlabel='Completed optimizer updates',ylabel='Validation NLL / UTF-8 byte (nats)',ylim=(0,2.3),xlim=(0,10000));left.grid(axis='y',alpha=.2);left.legend(loc='upper right',fontsize=8,frameon=False)
 values=[r['validation']['nllPerUtf8Byte'] for r in choice['rows']];bars=right.bar(['2,310','4,358'],values,color=['#94a3b8','#2563eb'],width=.6)
 right.set(xlabel='Own BPE vocabulary size',ylabel='Validation NLL / UTF-8 byte',ylim=(0,1.8),title='1,000-update pilots');right.bar_label(bars,labels=[f'{v:.3f}' for v in values],padding=4);right.grid(axis='y',alpha=.2);right.set_axisbelow(True)
 fig.suptitle('Own raw Japanese causal pretraining: held-document likelihood',fontsize=13,fontweight='medium');fig.text(.01,.02,'Byte normalization permits vocabulary comparison. Lower likelihood loss alone does not establish natural or meaningful generation.',fontsize=8,color='#475569');fig.tight_layout(rect=(0,.06,1,.95))
 save_svg(fig,ROOT/'raw-million'/'learning-curves.svg');fig.savefig(ROOT/'raw-million'/'learning-curves.png',dpi=180);plt.close(fig)
 provenance=dict(metricsSha256=hashlib.sha256(metrics.read_bytes()).hexdigest(),vocabularyChoiceSha256=hashlib.sha256((ROOT/'vocabulary-choice.json').read_bytes()).hexdigest(),lastRecordedUpdate=history[-1]['step'],noTestSelection=True,note='Original metrics plotted without smoothing. Parameter counts and byte exposure differ between vocabulary pilots. Likelihood is not a Japanese fluency or owner-QA score.')
 (ROOT/'raw-million'/'figure-sources.json').write_text(json.dumps(provenance,indent=2)+'\n')
 paragraph=ROOT/'paragraph-million'/'metrics.json'
 if paragraph.exists():
  data=json.loads(paragraph.read_text());history=data['history'];x=[r['step'] for r in history]
  fig,ax=plt.subplots(figsize=(8,4.8))
  for site in ['aozora','mdn','jma','maff']:ax.plot(x,[r['validation']['sites'][site]['nllPerUtf8Byte'] for r in history],color=colors[site],linewidth=1.5,label=labels[site])
  ax.plot(x,[r['validation']['nllPerUtf8Byte'] for r in history],color='#111827',linewidth=2.5,label='All held canonical paragraphs')
  ax.set(xlabel='Completed additional optimizer updates',ylabel='Validation NLL / UTF-8 byte (nats)',xlim=(0,10000));ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8,frameon=False)
  fig.suptitle('Own raw-paragraph continuation: held-document paragraph likelihood',fontsize=12)
  fig.text(.01,.02,'Paragraph EOS differs from whole-document EOS. Compare this run with its own initial point, not the preceding full-document PPL.',fontsize=8,color='#475569');fig.tight_layout(rect=(0,.06,1,.95))
  save_svg(fig,paragraph.parent/'learning-curves.svg');fig.savefig(paragraph.parent/'learning-curves.png',dpi=180);plt.close(fig)
  provenance=dict(metricsSha256=hashlib.sha256(paragraph.read_bytes()).hexdigest(),lastRecordedUpdate=history[-1]['step'],noTestSelection=True,unit='Canonical complete source paragraph',note='No smoothing. Paragraph and full-document likelihood objectives differ; a loss reduction does not prove grammatical or meaningful generation.')
  (paragraph.parent/'figure-sources.json').write_text(json.dumps(provenance,indent=2)+'\n')
if __name__=='__main__':main()
