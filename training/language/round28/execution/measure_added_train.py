"""Fixed128-human-TRAIN-dialogue postselection likelihood; not all TRAIN or TEST."""
import hashlib,pathlib,sys,json
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));import train as t
sys.path.insert(0,str(R.parent/'round10'));from evaluate import load_model
t.torch.set_num_threads(1);i,v=t.load_partition(R/'multiview','train');added=t.read(R/'multiview/data.json')['addedTrainViews'];sources=sorted({x['sourceDocument'] for x in added},key=lambda s:hashlib.sha256(('round28-fixed-train-diagnostic|'+s).encode()).hexdigest());selected=set(sources[:128]);ids={x['id'] for x in added if x['sourceDocument'] in selected};assert len(selected)==128 and len(ids)==384
i={k:[x for x in i[k] if (x['unit'] if k=='rows' else x['id']) in ids] for k in ['rows','documents']};assert len(i['documents'])==384
models={}
for n,p in [('old',R.parent/'round25/continue-10000/model.js'),('new',R/'continue-10000/model.js')]:
 m,e=load_model(p);models[n]=dict(modelSha256=t.sha(p),selectedStep=e['training']['bestStep'],metric=t.measure_views(m,i,v,8))
t.write(R/'execution/added-train-loss.json',dict(models=models,sourceIndexSha256=t.sha(R/'multiview/train.index.json'),populationUnitsPerView=len(sources),sampledUnitsPerView=128,sampledSourceIds=sources[:128],fixedSelection='Lowest128 SHA256(round28-fixed-train-diagnostic|sourceDocument), all3views and all windows of each; fixed before training',newHumanTrainSampleOnly=True,notFullExpandedTrainEstimate=True,trainingOnly=True,postSelectionDiagnostic=True,usedForSelection=False,teacherForcedNotAutoregressive=True,threads=1,sevenDecimalExports=True,additionalOptimizerUpdates=0))
print(json.dumps({n:d['metric']['nllPerUtf8Byte'] for n,d in models.items()}))
