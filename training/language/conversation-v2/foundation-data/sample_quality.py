"""Deterministic candidate TRAIN paragraphs; no quality-based redraw or admission."""
import argparse,gzip,hashlib,json,pathlib
HERE=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(corpus,output):
    if output.exists():raise ValueError('Refuse to overwrite a quality sample')
    plan=json.loads((HERE/'QUALITY_AUDIT_PLAN.json').read_text());best={}
    with gzip.open(corpus,'rt')as f:
        for line in f:
            d=json.loads(line)
            if d['split']!='train':continue
            for p in d['paragraphs']:
                text=p['normalizedText']
                if not p['keepForCandidateTraining']or not 80<=len(text)<=1200:continue
                h=hashlib.sha256(('foundation-quality-v1|'+d['source']+'|'+d['id']+'|'+str(p['ordinal'])).encode()).hexdigest()
                k=d['source'],d['component']
                r=dict(sampleHash=h,source=d['source'],id=d['id'],title=d['title'],family=d['family'],component=d['component'],paragraphOrdinal=p['ordinal'],text=text,sourceUrl=d['url'],revision=d['revision'],license=d['license'],humanStatus=d['humanStatus'],timestamp=d.get('timestamp'),lastContributorUsername=d.get('lastContributorUsername'),split='train')
                if k not in best or h<best[k]['sampleHash']:best[k]=r
    rows=[]
    for source,n in plan['selection']['maximumPerSource'].items():
        rows.extend(sorted([r for(k,_),r in best.items()if k==source],key=lambda r:r['sampleHash'])[:n])
    output.write_text(json.dumps(dict(planSha256=sha(HERE/'QUALITY_AUDIT_PLAN.json'),corpusSha256=sha(corpus),rows=rows,noModelOutputs=True),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(rows=len(rows),output=str(output),sha256=sha(output))))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--corpus',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();run(a.corpus,a.output)
