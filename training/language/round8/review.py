"""Aggregate explicit manual language judgments against the frozen gate.
No model output is edited, scored by gold equality, or fed back to training.
"""
import argparse,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--generation',type=pathlib.Path,required=True);parser.add_argument('--manual',type=pathlib.Path,required=True);parser.add_argument('--out',type=pathlib.Path,required=True);args=parser.parse_args()
 generation=json.loads(args.generation.read_text());manual=json.loads(args.manual.read_text());policy=json.loads((ROOT/'generation-policy.json').read_text());keys=['grammar','meaning','connection','repetition','breaks'];judgments={r['id']:r for r in manual['rows']}
 assert manual['generationSha256']==hashlib.sha256(args.generation.read_bytes()).hexdigest();assert set(judgments)=={r['id'] for r in generation['rows']};assert len(judgments)==len(manual['rows'])
 rows=[]
 for output in generation['rows']:
  j=judgments[output['id']];assert all(type(j[k]) is int and 0<=j[k]<=2 for k in keys);assert isinstance(j['fullOutputLoop'],bool);assert isinstance(j['sentenceClosed'],bool);assert j['reason']
  total=sum(j[k] for k in keys);passed=total>=policy['acceptance']['minimumTotalScore'] and j['grammar']>=policy['acceptance']['minimumGrammarScore'] and j['connection']>=policy['acceptance']['minimumConnectionScore'] and j['sentenceClosed'] and output['validTokens']
  rows.append(dict(**output,manual=j,totalScore=total,firstSentencePass=passed))
 def aggregate(selected):
  groups={}
  for name in ['narrative','contemporary-expository']:
   subset=[r for r in selected if (r['site']=='aozora')==(name=='narrative')];passed=sum(r['firstSentencePass'] for r in subset);no_loop=sum(not r['manual']['fullOutputLoop'] for r in subset)
   groups[name]=dict(total=len(subset),firstSentencePassed=passed,firstSentenceSuccessRate=passed/len(subset),fullOutputNonLoop=no_loop,fullOutputNonLoopRate=no_loop/len(subset),gatePassed=passed/len(subset)>=policy['acceptance']['minimumSentenceSuccessRate'] and no_loop/len(subset)>=policy['acceptance']['minimumFullOutputNonLoopRate'])
  return groups
 groups=aggregate(rows)
 old_policy=json.loads((ROOT.parent/'round6/generation-policy.json').read_text());core_ids={r['id'] for r in old_policy['probes'][generation['partition']]};core_rows=[r for r in rows if r['id'] in core_ids]
 assert len(core_rows)==len(core_ids)
 core_groups=aggregate(core_rows)
 report=dict(modelVersion=generation['modelVersion'],partition=generation['partition'],generationSha256=manual['generationSha256'],reviewer=manual['reviewer'],independentHumanEvaluation=False,total=len(rows),passed=sum(r['firstSentencePass'] for r in rows),validTokenOutputs=sum(r['validTokens'] for r in rows),groups=groups,coreGroups=core_groups,coreTotal=len(core_rows),corePassed=sum(r['firstSentencePass'] for r in core_rows),gatePassed=all(g['gatePassed'] for g in list(groups.values())+list(core_groups.values())),frozenAcceptance=policy['acceptance'],rows=rows,note='Assistant manual scoring, not independent blind human assessment. Original continuation is attribution/context only, not an exact-match answer. Grammar/meaning/connection/repetition/breaks are checked for the observed first sentence, and full output looping is additionally reported. Full raw outputs and all token IDs remain unedited; invalid UTF8/controls force failure. No judgment/TEST output trains or selects weights.')
 args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['total','passed','validTokenOutputs','groups','gatePassed']}))
if __name__=='__main__':main()
