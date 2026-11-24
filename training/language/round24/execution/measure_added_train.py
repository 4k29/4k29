"""Post-selection teacher-forced added TRAIN loss only; no TEST or optimizer."""
import pathlib,sys,json
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import train as t
sys.path.insert(0,str(R.parent/'round10'));from evaluate import load_model
t.torch.set_num_threads(1);i,v=t.load_partition(R/'multiview','train');ids={x['id'] for x in t.read(R/'multiview/data.json')['addedTrainViews']};i={k:[x for x in i[k] if (x['unit'] if k=='rows' else x['id']) in ids] for k in ['rows','documents']};assert len(i['documents'])==t.read(R.parent/'round22/sources/manifest.json')['admittedUnits']*3
models={}
for n,p in [('old',R.parent/'round23/continue-10000/model.js'),('new',R/'continue-10000/model.js')]:
 m,e=load_model(p);models[n]=dict(modelSha256=t.sha(p),selectedStep=e['training']['bestStep'],metric=t.measure_views(m,i,v,8))
t.write(R/'execution/added-train-loss.json',dict(models=models,sourceIndexSha256=t.sha(R/'multiview/train.index.json'),unitsPerView=t.read(R.parent/'round22/sources/manifest.json')['admittedUnits'],trainingOnly=True,postSelectionDiagnostic=True,usedForSelection=False,teacherForcedNotAutoregressive=True,threads=1,sevenDecimalExports=True,additionalOptimizerUpdates=0))
print(json.dumps({n:d['metric']['nllPerUtf8Byte'] for n,d in models.items()}))
