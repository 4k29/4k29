"""Aggregate frozen first-sentence AND whole-output gates at all three scopes."""
import argparse,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def review(generation,manual,policy,meaning,parent,original):
 keys=['grammar','meaning','connection','repetition','breaks'];judgments={r['id']:r for r in manual['rows']};assert len(judgments)==len(manual['rows']) and set(judgments)=={r['id'] for r in generation['rows']}
 rows=[]
 for output in generation['rows']:
  j=judgments[output['id']];assert all(type(j[k]) is int and 0<=j[k]<=2 for k in keys);assert all(type(j[k]) is bool for k in ['sentenceClosed','fullOutputLoop','fullOutputMeaningful']);assert j['reason']
  if not output['validTokens']:assert not j['fullOutputMeaningful']
  total=sum(j[k] for k in keys);passed=total>=policy['acceptance']['minimumTotalScore'] and j['grammar']>=policy['acceptance']['minimumGrammarScore'] and j['connection']>=policy['acceptance']['minimumConnectionScore'] and j['sentenceClosed'] and output['validTokens']
  rows.append(dict(**output,manual=j,totalScore=total,firstSentencePass=passed))
 def aggregate(selected):
  groups={}
  for name in ['narrative','contemporary-expository']:
   subset=[r for r in selected if (r['site']=='aozora')==(name=='narrative')];assert subset
   first=sum(r['firstSentencePass'] for r in subset);nonloop=sum(not r['manual']['fullOutputLoop'] for r in subset);semantic=sum(r['manual']['fullOutputMeaningful'] for r in subset);n=len(subset)
   groups[name]=dict(total=n,firstSentencePassed=first,firstSentenceSuccessRate=first/n,fullOutputNonLoop=nonloop,fullOutputNonLoopRate=nonloop/n,fullOutputMeaningful=semantic,fullOutputMeaningfulRate=semantic/n,gatePassed=first/n>=policy['acceptance']['minimumSentenceSuccessRate'] and nonloop/n>=policy['acceptance']['minimumFullOutputNonLoopRate'] and semantic/n>=meaning['minimumMeaningfulFullOutputRate'])
  return dict(total=len(selected),passed=sum(r['firstSentencePass'] for r in selected),fullOutputNonLoop=sum(not r['manual']['fullOutputLoop'] for r in selected),fullOutputMeaningful=sum(r['manual']['fullOutputMeaningful'] for r in selected),groups=groups,gatePassed=all(g['gatePassed'] for g in groups.values()))
 scopes={'expanded17':aggregate(rows)}
 for name,source in [('parent13',parent),('original9',original)]:
  ids={r['id'] for r in source['probes'][generation['partition']]};selected=[r for r in rows if r['id'] in ids];assert len(selected)==len(ids);scopes[name]=aggregate(selected)
 return dict(partition=generation['partition'],modelVersion=generation['modelVersion'],scopes=scopes,total=len(rows),passed=scopes['expanded17']['passed'],fullOutputNonLoop=scopes['expanded17']['fullOutputNonLoop'],fullOutputMeaningful=scopes['expanded17']['fullOutputMeaningful'],validTokenOutputs=sum(r['validTokens'] for r in rows),gatePassed=all(s['gatePassed'] for s in scopes.values()),naturalLanguageEstablished=all(s['gatePassed'] for s in scopes.values()),rows=rows,independentHumanEvaluation=False,note='Assistant manual scoring of unedited autoregressive continuations, not independent blind human evaluation. Short closure and nonloop do not prove sustained coherence. No judgment used for training or weight/vocabulary selection.')
def main():
 p=argparse.ArgumentParser();p.add_argument('--generation',type=pathlib.Path,required=True);p.add_argument('--manual',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);args=p.parse_args();generation=read(args.generation);manual=read(args.manual)
 assert manual['generationSha256']==sha(args.generation) and manual['meaningPolicySha256']==sha(ROOT/'full-meaning-policy.json')
 report=review(generation,manual,read(ROOT/'generation-policy.json'),read(ROOT/'full-meaning-policy.json'),read(ROOT.parent/'round8/generation-policy.json'),read(ROOT.parent/'round6/generation-policy.json'));report.update(generationSha256=sha(args.generation),meaningPolicySha256=sha(ROOT/'full-meaning-policy.json'),reviewer=manual['reviewer'])
 args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False))
if __name__=='__main__':main()
