"""Cold CI recomputation on full histories; discard logits after verification."""
from verify import V,base,bykey,plan
from run import torch,load_checkpoint,decoder

torch.set_num_threads(2)
torch.use_deterministic_algorithms(True)
calls=0
with torch.inference_mode():
    for name,ref in plan['models'].items():
        state=load_checkpoint(V/ref['path'],ref['sha'])
        model=decoder(state['trajectory']['config']).eval()
        model.load_state_dict(state['trajectory']['model'])
        del state
        for (n,i,a),r in bykey.items():
            if n!=name:continue
            prefix=base[n,i]['prefix']
            scores=model(torch.tensor([prefix+r['tokens'][:-1]]))[0,len(prefix)-1:]
            assert scores.argmax(-1).tolist()==r['replay_argmax']
            calls+=1
print('Cold model evaluation forwards:',calls,'optimizer calls: 0')
