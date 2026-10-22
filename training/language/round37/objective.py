"""Penalize only completions that repeat an observed fourgram; gold excluded."""
import torch
from torch.nn import functional as F

def negative_candidates(x,y,window=64):
    if window<1 or x.ndim!=2 or x.shape!=y.shape:raise ValueError('Invalid history or target shapes')
    # At t, history ends at x[t]. No x[t+1:] or future target is consulted.
    history=F.pad(x,(window+2,0),value=0).unfold(1,window+3,1)
    grams=history.unfold(-1,4,1)
    suffix=history[...,-3:]
    match=(grams[...,:3]==suffix.unsqueeze(-2)).all(-1)
    match=match & (suffix>=6).all(-1).unsqueeze(-1)
    ids=torch.where(match,grams[...,-1],0).sort(-1).values
    unique=torch.ones_like(ids,dtype=torch.bool)
    unique[...,1:]=ids[...,1:]!=ids[...,:-1]
    mask=unique & (ids>=6) & (ids!=y.unsqueeze(-1)) & y.ne(-100).unsqueeze(-1)
    return ids,mask

def causal_unlikelihood(logits,x,y,window=64):
    ids,mask=negative_candidates(x,y,window)
    logp=F.log_softmax(logits,dim=-1).gather(-1,ids)
    penalty=-torch.log1p(-logp.exp().clamp(max=1-1e-6))
    return (penalty*mask).sum()/y.ne(-100).sum().clamp_min(1),int(mask.sum())
