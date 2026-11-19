"""Record layer norms after applying the global clipping coefficient."""
from prepare import ROOT, read, save

def normalize():
    for path in sorted(ROOT.glob('?-*-grad.json')):
        data=read(path)
        global_metrics=data['global_metrics']
        for name in ('prose','replay','mixed'):
            key=f'{name}_norm'
            scale=min(1.,1./(global_metrics[key]+1e-6))
            for metrics in [global_metrics,*data['layers'].values()]:
                metrics.pop('mixed_norm_clipped_global',None)
                metrics[f'{name}_norm_after_global_clip']=metrics[key]*scale
        save(path,data)

if __name__=='__main__':
    normalize()
