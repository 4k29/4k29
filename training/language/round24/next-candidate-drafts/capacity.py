"""Draft: preserve old FFN function, add own random features with zero output."""
import torch

def expand_ffn_weights(model,parent):
    old_hidden=parent['config']['hidden'];new_hidden=model.config['hidden']
    assert new_hidden>old_hidden
    assert {k:v for k,v in model.config.items() if k!='hidden'}=={k:v for k,v in parent['config'].items() if k!='hidden'}
    current=model.state_dict()
    for name,old in parent['model'].items():
        new=current[name]
        if old.shape==new.shape:new.copy_(old)
        elif name.endswith('fc1.weight'):
            assert old.shape[1:]==new.shape[1:] and old.shape[0]==old_hidden and new.shape[0]==new_hidden
            new[:old_hidden].copy_(old)
        elif name.endswith('fc1.bias'):
            assert old.shape==(old_hidden,) and new.shape==(new_hidden,)
            new.zero_();new[:old_hidden].copy_(old)
        elif name.endswith('fc2.weight'):
            assert old.shape[0]==new.shape[0] and old.shape[1]==old_hidden and new.shape[1]==new_hidden
            new.zero_();new[:,:old_hidden].copy_(old)
        else:raise ValueError('Unexpected changed shape: '+name)
    model.load_state_dict(current)

def expand_optimizer_moments(optimizer,model,parent):
    # Call after loading the original parent optimizer state. Old coordinates retain
    # exact moments and global tensor age; new coordinates have zero moments.
    for name,p in model.named_parameters():
        old=parent['model'][name]
        if p.shape==old.shape:continue
        state=optimizer.state[p]
        for key in ['exp_avg','exp_avg_sq']:
            saved=state[key];assert saved.shape==old.shape
            padded=torch.zeros_like(p)
            if name.endswith(('fc1.weight','fc1.bias')):padded[:old.shape[0]].copy_(saved)
            elif name.endswith('fc2.weight'):padded[:,:old.shape[1]].copy_(saved)
            else:raise ValueError(name)
            state[key]=padded
