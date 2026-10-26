"""Frozen canonical human-role evaluation, isolated from original pilot results."""
import argparse,json,pathlib,sys,time,hashlib
import torch,numpy as np
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parent
sys.path.insert(0,str(BASE));sys.path.insert(0,str(BASE/'next_stage'))
from core import sha,digest,decoder,REPO
from eval_core import response_scores,greedy,groups,fence,byte_payload
from evaluate import summarize_responses
from rebase_roles import rebase_human_prefix
from eval_chunk_loader import load_chunks

def read(p):return json.loads(pathlib.Path(p).read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def rollout(model,cases,pieces,ids):
 out=[]
 for ident in ids:
  c=next(c for c in cases if c['id']==ident);prefix=c['prefixTokens'];turns=[];left=prefix[1:-1];role=prefix[-1]
  while left:
   e=left.index(2)+1;turns.append(left[:e]);left=left[e:]
  rows=[]
  for j in range(3):
   dropped=[]
   while 2+sum(map(len,turns))+64>256:dropped.append(turns.pop(0))
   raw=[1]+[t for q in turns for t in q]+[role];rebased,mapping=rebase_human_prefix(raw)
   if rebased!=raw:
    turns=[[7-t if t in(3,4)else t for t in q]for q in turns];role=7-role
   g=greedy(model,rebased,pieces,max_new=64)
   rows.append(dict(turn=j,inputTokens=rebased,inputBodyBytes=byte_payload(rebased,pieces),inputRoleMapping=mapping,droppedWholeTurns=dropped,localRoleToken=role,generation=g))
   if not g['eos']:break
   turns.append([role]+g['tokensIncludingEos']);role=7-role
  out.append(dict(id='selfplay-'+ident,sourceCaseId=ident,originalHumanHistory=c['history'],initialPrefixTokens=prefix,rows=rows,completedTurns=sum(r['generation']['eos']for r in rows),interpretation='Human A/B selfplay stress, not human-interactive AI response success'))
 return out

def run(a):
 plan=read(a.plan)
 if sha(a.plan)!=a.plan_sha:raise ValueError('Frozen evaluation plan SHA mismatch')
 for p,h in plan['codeReceipts'].items():
  if sha(REPO/p)!=h:raise ValueError('Code receipt mismatch '+p)
 panels=[read(HERE/'unified32-dev.json'),read(HERE/'content-dev.json')]
 for name,h in plan['panelSha256'].items():
  if sha(HERE/name)!=h:raise ValueError('Panel/rubric changed')
 out=HERE/'evaluation'/a.endpoint
 if out.exists():raise ValueError('Refuse evaluation overwrite')
 if a.manifest:
  archived=read(a.manifest)
  if archived['sha256']!=a.checkpoint_sha:raise ValueError('Checkpoint archive SHA mismatch')
  saved=load_chunks(a.manifest)
 else:
  if sha(a.checkpoint)!=a.checkpoint_sha:raise ValueError('Checkpoint SHA mismatch')
  saved=torch.load(a.checkpoint,map_location='cpu',weights_only=False)
 s=saved.get('trajectory',saved);config=s['config'];weights=s['model'];step=s.get('uniqueUpdates',saved.get('uniqueUpdates'))
 if step!=a.expected_updates:raise ValueError('Endpoint update mismatch')
 expected=read(BASE/'PLAN.json')['models'][a.model]
 if config!=expected:raise ValueError('Architecture mismatch')
 
 if sha(BASE/'data/data.json')!=plan['dataManifestSha256'] or sha(BASE/'data/tokenizer.json')!=plan['tokenizerSha256']:raise ValueError('Frozen input data/tokenizer mismatch')
 data=read(BASE/'data/data.json');tok=read(BASE/'data/tokenizer.json')
 if sha(BASE/'data/tokenizer.json')!=data['tokenizerSha256']:raise ValueError('Tokenizer mismatch')
 torch.set_num_threads(1);torch.use_deterministic_algorithms(True);rng=torch.get_rng_state().clone()
 model=decoder(config);model.load_state_dict(weights,strict=True);model.eval();torch.set_rng_state(rng);del saved,s,weights
 before=digest(model.state_dict());pieces=[bytes.fromhex(x)for x in tok['bytes']];started=time.monotonic();out.mkdir()
 response=[];generated=[];windows=[]
 # Fixed original windows are not reframed because they are arbitrary corpus slices.
 from eval_core import window_scores
 values=np.memmap(REPO/data['devTokensPath'],dtype='<u4',mode='r')
 for j,w in enumerate(data['devWindows']):
  seq=list(map(int,values[w['offset']:w['offset']+w['length']]));windows.append(dict(window=j,document=w['document'],**window_scores(model,seq,pieces)))
 for panel in panels:
  for c in panel['cases']:
   prefix=c['prefixTokens'];gold=c['goldTokens'];logits,scores=response_scores(model,prefix,gold,pieces)
   base=dict(id=c['id'],document=c['document'],history=c['history'],prefixText=c['prefixText'],prefixTokens=prefix,originalPrefixTokens=c['originalPrefixTokens'],roleMapping=c['roleMapping'],targetText=c['targetText'],goldTokens=gold,sourceSha256=c['sourceSha256'],category=c.get('category'),contentRequired=c.get('contentRequired'),minimumSemanticRequirement=c.get('minimumSemanticRequirement'),supported=True)
   response.append(dict(**base,scores=scores));generated.append(dict(**base,generationSupported=True,**greedy(model,prefix,pieces,gold,logits,max_new=192)))
 ids=read(BASE/'PLAN.json')['evaluation']['rolloutCaseIds'];rollouts=rollout(model,panels[0]['cases'],pieces,ids)
 summaries={}
 for panelname,panel in zip(['unified32','content24'],panels):
  valid={c['id']for c in panel['cases']};r=[r for r in response if r['id']in valid];g=[r for r in generated if r['id']in valid]
  summaries[panelname]=dict(responseCases=summarize_responses(r),generated=len(g),actualEos=sum(x['eos']for x in g),strictUtf8=sum(x['strictUtf8']for x in g),mechanicalRepeated4=sum(x['repeated4gram']is not None for x in g),meanBodyTokens=sum(x['generatedNonEosTokens']for x in g)/len(g),uniqueTexts=len({x['rawBytesHex']for x in g}),semanticScoring='Independent whole-output reading required; no automatic natural-language ability inference')
 summary=dict(endpoint=a.endpoint,model=a.model,updates=step,checkpointSha256=a.checkpoint_sha,panels=summaries,windowMetrics=groups([t for r in windows for t in r['tokens']]),selfplayEpisodes=4,selfplayTurns=sum(len(x['rows'])for x in rollouts),optimizerUpdates=0,sealedTestUsed=False)
 for name,obj in [('response-tf',response),('generations',generated),('window-tf',windows),('selfplay',rollouts),('summary',summary)]:write(out/(name+'.json'),obj)
 md=['# Full unmodified canonical-role generations','All outputs preserved; source human-A/B continuation, not AI identity claims.']
 for g in generated:md += ['','## '+g['id'],'History:',fence(g['prefixText']),'Output:',fence(g['text']if g['strictUtf8']else g['rawBytesHex']),'All IDs incl EOS:',fence(json.dumps(g['tokensIncludingEos']))]
 for ep in rollouts:
  md += ['','## '+ep['id'],fence('\n'.join(x['text']for x in ep['originalHumanHistory']))]
  for row in ep['rows']:
   g=row['generation'];md += ['Turn '+str(row['turn']),fence(g['text']if g['strictUtf8']else g['rawBytesHex']),fence(json.dumps(g['tokensIncludingEos']))]
 (out/'ALL_GENERATIONS.md').write_text('\n'.join(md)+'\n')
 assert before==digest(model.state_dict())and torch.equal(rng,torch.get_rng_state())
 write(out/'receipt.json',dict(status='complete',endpoint=a.endpoint,model=a.model,uniqueUpdates=step,checkpointSha256=a.checkpoint_sha,evaluationPlanSha256=a.plan_sha,modelAndRngUnchanged=True,elapsedSeconds=time.monotonic()-started,optimizerUpdates=0,sealedTestUsed=False,generatedCases=len(generated),windowRows=len(windows),selfplayEpisodes=len(rollouts),selfplayTurns=sum(len(x['rows'])for x in rollouts)))
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--plan',type=pathlib.Path,required=True);p.add_argument('--plan-sha',required=True);p.add_argument('--model',choices=['small','medium'],required=True);p.add_argument('--endpoint',required=True);p.add_argument('--expected-updates',type=int,required=True);p.add_argument('--checkpoint-sha',required=True);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--checkpoint',type=pathlib.Path);g.add_argument('--manifest',type=pathlib.Path);run(p.parse_args())
