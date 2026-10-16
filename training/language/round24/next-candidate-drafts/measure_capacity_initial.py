"""Zero experimental updates: own real parent expanded FFN function/moment audit."""
import pathlib,sys,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import train as t
from capacity import expand_ffn_weights,expand_optimizer_moments
t.torch.set_num_threads(1)
parent_path=R.parent/'round11/continue-10000/checkpoint.pt';parent=t.torch.load(parent_path,map_location='cpu',weights_only=False)
old=t.Decoder(parent['config']);old.load_state_dict(parent['model']);old.eval();t.torch.manual_seed(2049)
new=t.Decoder(dict(parent['config'],hidden=1536));expand_ffn_weights(new,parent);new.eval()
opt=t.torch.optim.AdamW(new.parameters(),lr=t.read(R/'policy.json')['learningRate'],weight_decay=.05);opt.load_state_dict(parent['optimizer']);expand_optimizer_moments(opt,new,parent)
for name,p in new.named_parameters():
 state=opt.state[p];source=parent['model'][name];assert int(state['step'])==10000
 for key in ['exp_avg','exp_avg_sq']:
  value=state[key];assert value.shape==p.shape and t.torch.isfinite(value).all()
  if value.shape!=source.shape:
   kept=value[:source.shape[0]] if name.endswith(('fc1.weight','fc1.bias')) else value[:,:source.shape[1]]
   added=value[source.shape[0]:] if name.endswith(('fc1.weight','fc1.bias')) else value[:,source.shape[1]:]
   assert not t.torch.count_nonzero(added)
   source_ids=list(parent['model']).index(name);assert t.torch.equal(kept,parent['optimizer']['state'][source_ids][key])
info,values=t.load_partition(R/'multiview','train');rows=[next(row for row in info['rows'] if row['variant']==v) for v in range(3)];x,y=t.pack(rows,values,256);errors=[]
for length in [32,64,128]:
 with t.torch.no_grad():a=old(x[:,:length]);b=new(x[:,:length])
 error=float((a-b).abs().max());assert error<=2e-4
 errors.append(dict(length=length,maxAbsoluteLogitError=error,allPositionsArgmaxEqual=bool(t.torch.equal(a.argmax(-1),b.argmax(-1)))))
new.train();t.torch.set_rng_state(parent['torchRng']);z=new(x[:,:64]);loss=t.F.cross_entropy(z.flatten(0,1),y[:,:64].flatten());loss.backward()
assert all(p.grad is not None and t.torch.isfinite(p.grad).all() and p.grad.abs().sum()>0 for p in new.parameters())
for block in new.blocks:
 assert not t.torch.count_nonzero(block.fc1.weight.grad[768:])
 assert t.torch.count_nonzero(block.fc2.weight.grad[:,768:])>0
record=dict(parentCheckpointSha256=t.sha(parent_path),oldParameters=sum(p.numel() for p in old.parameters()),newParameters=sum(p.numel() for p in new.parameters()),oldHidden=768,newHidden=1536,embedding=192,layers=8,context=256,oldWeightsAndMomentsKept=True,newIncomingOwnRandomWeights=True,newOutgoingColumnsExactlyZero=True,newCoordinateMomentsExactlyZero=True,allParametersFiniteNonzeroGradientTotals=True,newIncomingGradientZeroAtFirstStepExpected=True,newOutgoingGradientsNonzero=True,initialFunctionErrors=errors,experimentalOptimizerUpdates=0,globalAdamWTensorCountersInherited=10000,newCoordinatesHaveNoIndependentAgeCounter=True,existingCoordinateLineage=49000,newCoordinateLineage=0,threads=1,trainOnly=True,testEncodedOrScoredOrGenerated=False)
p=pathlib.Path(__file__).resolve().with_name('capacity-initial-audit.json');p.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
