"""TRAIN original-unit EOS calibration only; no new training or language score."""
import pathlib,json,hashlib,sys,numpy as np,torch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from train import Decoder,pack
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();torch.set_num_threads(1)
i=read(R/'multiview/train.index.json');v=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');chosen=[]
for site in sorted({r['site'] for r in i['rows']}):
 candidates=[r for r in i['rows'] if r['site']==site and r['variant']==0 and int(v[r['offset']+r['length']-1])==2]
 chosen.append(min(candidates,key=lambda r:hashlib.sha256(('r30-fixed-eos-train|'+json.dumps(r,sort_keys=True)).encode()).hexdigest()))
paths={'initialOwnParent':R.parent/'round11/continue-10000/checkpoint.pt','adoptedRound25':R.parent/'round25/continue-10000/checkpoint.pt'}
if '--after' in sys.argv:paths['round30']=R/'continue-10000/checkpoint.pt'
models={}
for name,path in paths.items():
 c=torch.load(path,map_location='cpu',weights_only=False);m=Decoder(c['config']);m.load_state_dict(c['model'] if name=='initialOwnParent' else c['beststate']);m.eval();out=[]
 for row in chosen:
  x,y=pack([row],v,m.config['context']);position=row['length']-2;assert y[0,position]==2
  with torch.no_grad():z=m(x)[0,position];p=z.softmax(-1);rank=int((z>z[2]).sum())+1
  out.append(dict(sourceRow=row,pEos=float(p[2]),eosRank=rank,greedyToken=int(z.argmax()),goldEos=True))
 models[name]=dict(checkpointSha256=sha(path),checkpointActualStep=c['step'],weights='latest aligned' if name=='initialOwnParent' else 'selected beststate',selectedStep=c['step'] if name=='initialOwnParent' else c['beststep'],rows=out,meanEosProbability=sum(x['pEos'] for x in out)/len(out),greedyEos=sum(x['greedyToken']==2 for x in out))
out=dict(models=models,trainOnly=True,additionalOptimizerUpdates=0,sample='lowest SHA256(r30-fixed-eos-train|sorted-row-json) canonical real EOS-ending row per8sourcegenres; fixed before outcomes',notConversationTurnEndEvaluation=True,notAllTrainEstimate=True,notLanguageScore=True,notUsedForSelection=True,generatedTextsRepaired=False,trainingIndexSha256=sha(R/'multiview/train.index.json'))
(R/'execution'/('eos-prediction-comparison.json' if '--after' in sys.argv else 'pretraining-eos-prediction.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({n:{k:x[k] for k in ['meanEosProbability','greedyEos']} for n,x in models.items()}))
