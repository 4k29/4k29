"""Use the pre-isolated Part 2 panel only after the terminal checkpoint."""
from study import ROOT,OLD,prior,read,sha

def main():
    assert sha(ROOT/'DEV_PART2.json')==(ROOT/'DEV_PART2.sha256').read_text().strip()
    rows=read(ROOT/'DEV_PART2.json')['cases']
    rows=[r for r in rows if r['group']=='no_known_train_match']
    for key,folder in [('A',OLD/'artifacts/C-600'),('B',ROOT/'artifacts/B-600')]:
        model,_,_=prior.start(folder)
        ev=prior.lr.broad.evaluation
        ev.P=ROOT
        ev.train=[]
        ev.plan={'models':{}}
        ev.ev=dict(prose=[dict(r,prefix=r['full'],tokens=r['full']+r['gold'],teacher_continuation=r['gold'][:32]) for r in rows],caption=[])
        ev.restore=lambda _: (model,None,None)
        ev.evaluate(f'part2-heldout-{key}')

if __name__=='__main__':
    main()
