"""Posthoc matched5000 TRAIN-position EOS diagnostic; not generation or language grading."""
import pathlib,sys,json,hashlib,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round36';sys.path.insert(0,str(R));from train import Decoder,load_partition,pack,read,sha
from utterance_end_objective import eligible_mask
torch.set_num_threads(1);info,values=load_partition(R/'multiview','train');ends=read(R/'human-turn-token-boundaries.json')['boundariesByUnit'];salt='r35-posthoc-train-eos-location-v1'
key=lambda r:hashlib.sha256((salt+'|'+r['unit']+'|'+str(r['start'])).encode()).hexdigest()
rows=[r for variant in range(3)for r in sorted((r for r in info['rows']if r['site']=='human-chat'and r['variant']==variant),key=key)[:4]]
x,y=pack(rows,values,256);mask=eligible_mask(rows,y,ends);pieces=read(R/'multiview/tokenizer.json')['bytes'];non_newline=torch.tensor([i>=6 and b'\n'not in bytes.fromhex(t)for i,t in enumerate(pieces)]);safe_y=y.clamp_min(0);categories=dict(eligibleTrueTurnEnd=mask,otherOriginalNonStandaloneNewlineTargets=y.ge(6)&~mask&y.ne(16),nonNewlineOriginalContent=y.ge(6)&non_newline[safe_y],originalDialogueEos=y.eq(2));results={};paths={'retainedNewlineCeRound36':P/'execution/retained-paired-5000/checkpoint.pt','excludedNewlineCeRound37':E/'retained-paired-5000/checkpoint.pt'}
integrity=read(E/'eos-location-control-integrity.json')
for label,path in paths.items():
 if label in integrity['controls']:
  prior=integrity['controls'][label];assert sha(path)==prior['checkpointSha256']and sha(R/prior['frozenArtifactManifest'])==prior['frozenArtifactManifestSha256']
 else:assert label=='excludedNewlineCeRound37'and sha(path)==read(E/'retained-paired-5000/snapshot.json')['checkpointSha256']
 cp=torch.load(path,weights_only=False,map_location='cpu');assert cp['step']==5000;assert sorted({int(t['step'])for t in cp['optimizer']['state'].values()})==[25000];m=Decoder(cp['config']);m.load_state_dict(cp['model']);m.eval()
 with torch.no_grad():
  z=m(x);lp=z.log_softmax(-1);groups={}
  for name,c in categories.items():
   n=int(c.sum());data=dict(positions=n)
   if n:data.update(meanEosProbability=float(lp[:,:,2][c].exp().mean()),meanEosLogProbability=float(lp[:,:,2][c].mean()),eosArgmaxPositions=int((z.argmax(-1)[c]==2).sum()),meanOriginalGoldNll=float(-lp[c].gather(-1,y[c].unsqueeze(-1)).mean()))
   groups[name]=data
 results[label]=dict(checkpointSha256=sha(path),actualUpdates=5000,groups=groups)
 del m,cp
out=dict(controlIntegritySha256=sha(E/'eos-location-control-integrity.json'),actualUpdatesEach=5000,trainOnlyRows=rows,selectionSalt=salt,selection='First4 human TRAIN rows per view by fixed salted unit/start SHA, same fixed rows previously used for Round35 posthoc diagnostic; Round37 comparison planned before its5000 updates; independent of model outputs',trainIndexSha256=sha(R/'multiview/train.index.json'),trainTokensSha256=info['tokensSha256'],featureSha256=sha(R/'human-turn-token-boundaries.json'),results=results,modelMode='eval, one CPU thread, own raw FP32 weights, no sampling or generated targets',categoryCaution='Other nonstandalone targets can contain compound newline tokens; separate nonNewlineOriginalContent excludes all newline bytes but EOS argmax there is not by itself proof an alternative continuation is ungrammatical',posthocExploratory=True,notIndependentReplication=True,notSemanticOrGeneralizationEvidence=True,noHeldoutOpened=True,additionalOptimizerUpdates=0,codeSha256=sha(pathlib.Path(__file__)))
(E/'eos-location-effect-5000.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(actualUpdatesEach=5000,rows=len(rows),results=results)))
