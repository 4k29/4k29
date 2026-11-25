"""Evaluate identical targets at both lengths and with restored absolute positions."""
import sys
from study import ROOT,BASE,OLD,prior,torch,read,save,sha,recover

def shifted_nll(model,row):
    def preserve_positions(module,args):
        return (args[0]+row['cut'],)
    handle=model.position.register_forward_pre_hook(preserve_positions)
    try:
        with torch.inference_mode():
            prefix=row['short']
            gold=row['gold']
            seq=prefix+gold
            z=model(torch.tensor([seq[:-1]]))[0,len(prefix)-1:].double().log_softmax(-1)
            return [-float(z[i,t]) for i,t in enumerate(gold)]
    finally:
        handle.remove()

def main():
    dev=read(ROOT/'DEV.json')
    assert sha(ROOT/'DEV.json')==(ROOT/'DEV.sha256').read_text().strip()
    paths={'start':prior.parent,'control':OLD/'artifacts/C-600',
           'shortened':BASE/'prose-context-length/artifacts/B-600'}
    for key,folder in paths.items():
        model,_,_=prior.start(folder)
        model.eval()
        ev=prior.lr.broad.evaluation
        ev.P=ROOT
        ev.train=[]
        ev.plan={'models':{}}
        ev.ev=dict(prose=[dict(row,id=f"{row['id']}:{length}",prefix=row[length],tokens=row[length]+row['gold'],
                               teacher_continuation=row['gold'][:32])
                          for row in dev['cases'] for length in ('full','short')],caption=[])
        ev.restore=lambda _: (model,None,None)
        ev.evaluate(f'part1-{key}')
        positions={r['id']:shifted_nll(model,r) for r in dev['cases']}
        save(ROOT/f'part1-{key}-positions.json',positions)
        print(key,flush=True)

if __name__=='__main__':
    main()
