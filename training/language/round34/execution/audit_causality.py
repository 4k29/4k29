"""Read-only future-token perturbation on own initial model; not a language test."""
import pathlib,sys,json,hashlib,torch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R.parent));from model import Decoder
torch.set_num_threads(1);p=R/'continue-10000/checkpoint-0.pt';s=torch.load(p,map_location='cpu',weights_only=False);assert s['step']==0;m=Decoder(s['config']);m.load_state_dict(s['model']);m.eval();x=torch.arange(6,70,dtype=torch.long).unsqueeze(0);y=x.clone();y[:,32:]=(y[:,32:]+257)%(s['config']['vocabulary']-6)+6
with torch.no_grad():a,b=m(x),m(y)
error=float((a[:,:32]-b[:,:32]).abs().max());suffix=float((a[:,32:]-b[:,32:]).abs().max());assert error==0.0 and suffix>0
out=dict(sourceSnapshotActualStep=0,sourceCheckpointSha256=hashlib.sha256(p.read_bytes()).hexdigest(),modelCodeSha256=hashlib.sha256((R.parent/'model.py').read_bytes()).hexdigest(),testedTokens=64,sharedPrefixTokens=32,changedFutureTokens=32,prefixLogitMaxAbsoluteDifference=error,suffixLogitMaxAbsoluteDifference=suffix,causalPrefixInvariantForThisProbe=True,mode='eval/no_grad',inputKind='deterministic numeric own-vocabulary IDs, never TRAIN targets',notLanguageAbilityEvidence=True,noDevOrTestTextUsed=True,additionalOptimizerUpdatesByDiagnostic=0)
(R/'execution/causality-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
