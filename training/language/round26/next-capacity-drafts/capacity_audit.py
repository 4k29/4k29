"""Old-coordinate equality and new-coordinate birth bookkeeping for FFN-only expansion."""
import torch

def old_region(name,tensor,parent_tensor):
 if tensor.shape==parent_tensor.shape:return tensor
 if name.endswith(('fc1.weight','fc1.bias')):return tensor[:parent_tensor.shape[0]]
 if name.endswith('fc2.weight'):return tensor[:,:parent_tensor.shape[1]]
 raise AssertionError(name)

def new_region(name,tensor,parent_tensor):
 if tensor.shape==parent_tensor.shape:return tensor.flatten()[:0]
 if name.endswith(('fc1.weight','fc1.bias')):return tensor[parent_tensor.shape[0]:]
 if name.endswith('fc2.weight'):return tensor[:,parent_tensor.shape[1]:]
 raise AssertionError(name)

def verify_initial_expansion(zero,parent):
 assert zero['config']['hidden']==1536 and parent['config']['hidden']==768
 assert {k:v for k,v in zero['config'].items() if k!='hidden'}=={k:v for k,v in parent['config'].items() if k!='hidden'}
 assert zero['step']==0 and parent['step']==10000
 assert zero['pythonRng']==parent['pythonRng'] and torch.equal(zero['torchRng'],parent['torchRng'])
 names=list(parent['model']);assert names==list(zero['model'])
 for name,old in parent['model'].items():
  new=zero['model'][name];assert torch.equal(old_region(name,new,old),old),name
  if name.endswith(('fc1.bias','fc2.weight')):assert torch.count_nonzero(new_region(name,new,old))==0,name
 assert zero['optimizer']['param_groups']==parent['optimizer']['param_groups']
 for key,oldstate in parent['optimizer']['state'].items():
  name=names[key];newstate=zero['optimizer']['state'][key]
  for kind,old in oldstate.items():
   new=newstate[kind]
   if kind=='step':assert torch.equal(old,new)
   else:
    assert torch.equal(old_region(name,new,old),old),(name,kind)
    assert torch.count_nonzero(new_region(name,new,old))==0,(name,kind)
 assert sum(t.numel() for t in zero['model'].values())==7021248
 with torch.random.fork_rng(devices=[]):
  import sys,pathlib
  sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
  from model import Decoder
  torch.manual_seed(2049);fresh=Decoder(zero['config']).state_dict()
 for name,old in parent['model'].items():
  if name.endswith('fc1.weight'):
   features=new_region(name,zero['model'][name],old);assert torch.count_nonzero(features)>0
   assert torch.equal(features,new_region(name,fresh[name],old)),name
 return dict(oldCoordinatesWeightsAndMomentsExactlyPreserved=True,newIncomingOwnSeededFeatures=True,newOutgoingAndBiasZero=True,newMomentCoordinatesZero=True,torchAndPythonRngExactlyPreserved=True,oldCoordinateInitialLineage=49000,newCoordinateInitialLineage=0,adamWTensorCounterInherited=10000,newCoordinateIndependentAdamWAge=False)
