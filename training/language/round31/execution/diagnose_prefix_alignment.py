"""Fixed TRAIN-only context sensitivity; no generated targets or optimizer."""
import argparse,collections,hashlib,json,pathlib,sys,torch,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';sys.path.insert(0,str(R));import train as t
torch.set_num_threads(1);p=argparse.ArgumentParser();p.add_argument('--after',action='store_true');a=p.parse_args();read=t.read;sha=t.sha
C=R.parent/'round25';i=read(C/'multiview/train.index.json');values=np.memmap(C/'multiview/train.tokens.bin',dtype='<u4',mode='r');selected=[]
for site in sorted({r['site'] for r in i['rows']}):
 candidates=[r for r in i['rows'] if r['site']==site and r['variant']==0 and r['start']==0 and r['length']>=65];candidates.sort(key=lambda x:hashlib.sha256(('r31-fixed-context|'+json.dumps(x,sort_keys=True)).encode()).hexdigest());pair=[]
 for row in candidates:
  if not any(x['document']==row['document'] for x in pair):pair.append(row)
  if len(pair)==2:break
 assert len(pair)==2
 for j,row in enumerate(pair):selected.append(dict(target=row,donor=pair[1-j]))
plan=dict(trainOnly=True,selection='Two lowest SHA256(r31-fixed-context|sorted-row-JSON) canonical start0 length>=65 windows per genre, distinct source documents; swap32-token prefix within each pair.',selectionCommittedBeforeOutcomes=True,sourceIndexSha256=sha(C/'multiview/train.index.json'),sourceTokensSha256=sha(C/'multiview/train.tokens.bin'),prefixTokens=32,realContinuationTargets=32,rows=selected,notUnseenGeneralization=True,notSemanticAccuracy=True,noOptimizer=True,noTest=True)
planpath=E/'prefix-alignment-plan.json'
if planpath.exists():assert read(planpath)==plan
else:t.write(planpath,plan);print('PLAN_WRITTEN; run again after commit before measuring outcomes',flush=True);raise SystemExit(0)
models=[('initialOwnParent',R.parent/'round11/continue-10000/checkpoint.pt','model'),('round25',C/'continue-10000/checkpoint.pt','beststate'),('round30',R.parent/'round30/continue-10000/checkpoint.pt','beststate')]
if a.after:models.append(('round31',R/'continue-10000/checkpoint.pt','beststate'))
results={}
for name,path,key in models:
 cp=torch.load(path,map_location='cpu',weights_only=False)
 if name=='round31':assert cp['step']==10000
 m=t.Decoder(cp['config']);m.load_state_dict(cp[key]);m.eval();out=[]
 for pair in selected:
  row=pair['target'];donor=pair['donor'];seq=np.array(values[row['offset']:row['offset']+64],dtype=np.int64);target=seq[32:64].copy();wrong=seq.copy();wrong[:32]=values[donor['offset']:donor['offset']+32]
  x=torch.tensor(np.stack([seq[:-1],wrong[:-1]]));y=torch.tensor(target)
  with torch.no_grad():z=m(x)[:,31:63];loss=torch.nn.functional.cross_entropy(z.reshape(-1,cp['config']['vocabulary']),y.repeat(2),reduction='none').reshape(2,32)
  metrics={}
  for label,l in [('originalPrefix',loss[0]),('otherSourceSameGenrePrefix',loss[1])]:metrics[label]=dict(firstToken=float(l[0]),first8=float(l[:8].mean()),later24=float(l[8:].mean()),all32=float(l.mean()))
  out.append(dict(site=row['site'],source=row['document'],donorSource=donor['document'],**metrics))
 aggregate={label:{window:sum(row[label][window] for row in out)/len(out) for window in ['firstToken','first8','later24','all32']} for label in ['originalPrefix','otherSourceSameGenrePrefix']}
 results[name]=dict(checkpointSha256=sha(path),actualStep=cp['step'],selectedStep=cp['beststep'] if key=='beststate' else cp['step'],rows=out,meanTokenNll=aggregate)
 del m,cp
record=dict(planSha256=sha(planpath),models=results,trainOnly=True,notConversationAccuracy=True,notUnseenGeneralization=True,additionalOptimizerUpdates=0,notUsedForSelection=True,prefixSubstitutionIsArtificial=True,interpretation='Measures conditional sensitivity on a small actual-TRAIN sample. Better true-prefix likelihood does not prove coherent free generation, nor isolate semantic from lexical/source cues.')
t.write(E/'prefix-alignment-results.json',record);print(json.dumps({k:v['meanTokenNll'] for k,v in results.items()}),flush=True)
