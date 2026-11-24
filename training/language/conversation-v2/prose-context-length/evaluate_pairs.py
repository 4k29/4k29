"""Score the same original target tokens under full and shortened histories."""
from train import ROOT, OLD, prior, read

def generate(model,label,cases,folder):
    ev=prior.lr.broad.evaluation
    ev.P=folder
    ev.train=[]
    ev.plan={'models':{}}
    ev.ev=dict(prose=cases,caption=[])
    ev.restore=lambda _: (model,None,None)
    ev.evaluate(label)

def main():
    out=ROOT/'paired'
    out.mkdir(exist_ok=False)
    pairs=read(ROOT/'PAIRS.json')
    for arm,checkpoint in [('A',OLD/'artifacts/C-600'),('B',ROOT/'artifacts/B-600')]:
        model,_,_=prior.start(checkpoint)
        cases=[]
        for r in pairs:
            for name in ('full','short'):
                prefix=r[name]
                gold=r['targets']
                cases.append(dict(id=f"{r['id']}:{name}",prefix=prefix,tokens=prefix+gold,
                                  teacher_continuation=gold[:32],maxNewTokens=min(64,257-len(r['full']))))
        generate(model,arm,cases,out)
        if arm=='B':
            cases=[]
            for r in read(OLD/'HELDOUT.json'):
                cases.append(dict(r,tokens=r['prefix']+r['gold'],teacher_continuation=r['gold'][:32]))
            generate(model,'heldout-B-600',cases,out)

if __name__=='__main__':
    main()
