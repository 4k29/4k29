"""Sparse causal token unlikelihood; human source targets remain unchanged."""
import torch
from torch.nn import functional as F

def negative_candidates(x,y,window=64):
    if window<1 or x.shape!=y.shape:raise ValueError('Invalid history or target shapes')
    # At prediction t, x[t] is already observed; x[t+1:] is never consulted.
    history=F.pad(x,(window-1,0),value=0).unfold(1,window,1)
    ids=history.sort(dim=-1).values
    unique=torch.ones_like(ids,dtype=torch.bool)
    unique[...,1:]=ids[...,1:]!=ids[...,:-1]
    mask=unique & (ids>=6) & (ids!=y.unsqueeze(-1)) & y.ne(-100).unsqueeze(-1)
    return ids,mask

def causal_unlikelihood(logits,x,y,window=64):
    ids,mask=negative_candidates(x,y,window)
    logp=F.log_softmax(logits,dim=-1).gather(-1,ids)
    # Frozen float32 cap prevents log(0) for saturated predictions.
    penalty=-torch.log1p(-logp.exp().clamp(max=1-1e-6))
    loss=(penalty*mask).sum()/y.ne(-100).sum().clamp_min(1)
    return loss,int(mask.sum())
