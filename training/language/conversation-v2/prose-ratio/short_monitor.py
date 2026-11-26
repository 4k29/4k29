"""Score the body of the five inherited short monitor texts."""
import statistics

from run import ROOT,PREV,dump,git_checkpoint,old,read,restore,start,torch

@torch.inference_mode()
def main():
    cases=[r for r in read(PREV/'MONITOR.json') if r['id'].startswith('monitor:stair:')]
    specs={'start':None,'A-1967':PREV/'artifacts/A-1967','A-2950':PREV/'artifacts/A-2950',
           'B-1959':ROOT/'artifacts/B-1959','B-2935':ROOT/'artifacts/B-2935'}
    result={}
    for label,folder in specs.items():
        if folder is None:m,_,_=start()
        else:m,_=restore('A',git_checkpoint(folder))
        m.eval()
        rows=[]
        for row in cases:
            text=row['prefix']+row['gold']
            assert text[-1]==2
            prefix=text[:4]
            gold=text[4:]
            refs=old['gold_scores'](m,prefix,gold)
            rows.append(dict(id=row['id'],prefix=prefix,gold=gold,refs=refs))
        lp=[-value for r in rows for token,value in zip(r['gold'],r['refs']) if token>=6 and token!=16]
        result[label]=dict(nll=statistics.mean(lp),positions=len(lp),rows=rows)
    dump(ROOT/'SHORT_BODY_NLL.json',result)

if __name__=='__main__':main()
