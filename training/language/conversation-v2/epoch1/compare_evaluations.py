"""Descriptive paired mechanics; semantic success requires independent reading."""
import json,pathlib
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parent

def read(p):return json.loads(p.read_text())
def nll(rows):
 ts=[t for r in rows for t in r['scores']['tokens']];return sum(t['nll']for t in ts)/len(ts)
def mechanical(g):return dict(eos=bool(g['eos']),repeated4gram=g['repeated4gram']is not None,bodyTokens=g['generatedNonEosTokens'],strictUtf8=g['strictUtf8'])
def compare(a,b,ids):
 ar={x['id']:x for x in read(a/'response-tf.json')};br={x['id']:x for x in read(b/'response-tf.json')};ag={x['id']:x for x in read(a/'generations.json')};bg={x['id']:x for x in read(b/'generations.json')}
 return dict(cases=len(ids),bodyNllBefore=nll([ar[i]for i in ids]),bodyNllAfter=nll([br[i]for i in ids]),changedOutputs=sum(ag[i]['tokensIncludingEos']!=bg[i]['tokensIncludingEos']for i in ids),pairedCases=[dict(id=i,bodyNllBefore=ar[i]['scores']['body']['nllPerToken'],bodyNllAfter=br[i]['scores']['body']['nllPerToken'],generatedTokensBefore=ag[i]['tokensIncludingEos'],generatedTokensAfter=bg[i]['tokensIncludingEos'],textBefore=ag[i]['text'],textAfter=bg[i]['text'],before=mechanical(ag[i]),after=mechanical(bg[i]))for i in ids])
def main():
 old=read(HERE/'unified32-dev.json')['cases'];new=read(HERE/'content-dev.json')['cases'];out={}
 for m in ['small','medium']:
  base=HERE/'evaluation'/(m+'-512')
  if not base.exists():continue
  out[m]={'framingOriginalVsUnified32':compare(BASE/'evaluation'/m,base,[c['id']for c in old])}
  end=HERE/'evaluation'/(m+'-epoch1')
  if end.exists():out[m]['unified512VsEpoch1']={panel:compare(base,end,[c['id']for c in cases])for panel,cases in [('unified32',old),('content24',new)]}
 (HERE/'evaluation-comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({m:{k:{p:v for p,v in x.items()if p!='pairedCases'}for k,x in d.items()if k=='framingOriginalVsUnified32'}for m,d in out.items()}))
if __name__=='__main__':main()
