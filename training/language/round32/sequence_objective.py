"""self-generated repeats are negatives only; no generated CE targets."""
import torch
from torch.nn import functional as F
# Own causal fourgram implementation; generated tokens are negative candidates only.
from objective import negative_candidates

def repeated_generated_positions(tokens,prefix_length,window=64):
    if tokens.ndim!=2 or tokens.shape[0]!=1 or not 1<=prefix_length<tokens.shape[1]:
        raise ValueError('Require one contiguous nonempty prefix and generated suffix')
    x,y=tokens[:,:-1],tokens[:,1:]
    ids,mask=negative_candidates(x,torch.zeros_like(y),window)
    repeated=((ids==y.unsqueeze(-1)) & mask).any(-1)
    generated=torch.arange(y.shape[1],device=y.device).unsqueeze(0)>=prefix_length-1
    return repeated & generated,generated

def sequence_unlikelihood(logits,tokens,prefix_length,window=64):
    repeated,generated=repeated_generated_positions(tokens,prefix_length,window)
    if logits.shape[:2]!=tokens[:,:-1].shape:raise ValueError('Misaligned prediction positions')
    logp=F.log_softmax(logits,-1).gather(-1,tokens[:,1:].unsqueeze(-1)).squeeze(-1)
    loss=(-torch.log1p(-logp.exp().clamp(max=1-1e-6))*repeated).sum()/generated.sum().clamp_min(1)
    return loss,int(repeated.sum()),int(generated.sum())

def rollout_unlikelihood(model,prefix,max_new_tokens=64,eos=2,window=64):
    if prefix.ndim!=2 or prefix.shape[0]!=1 or prefix.shape[1]<1 or max_new_tokens<1:
        raise ValueError('Require one true prefix and positive rollout length')
    if prefix.shape[1]+max_new_tokens>model.config['context']:raise ValueError('Context overflow')
    was_training=model.training
    try:
        # Additional regularizer does not consume global dropout RNG of the CE run.
        with torch.random.fork_rng(devices=[]):
            model.eval();tokens=prefix.detach().clone()
            with torch.no_grad():
                for _ in range(max_new_tokens):
                    nxt=model(tokens)[:,-1].argmax(-1,keepdim=True)
                    tokens=torch.cat([tokens,nxt],-1)
                    if int(nxt[0,0])==eos:break
            model.eval()  # Negative scoring matches rollout mode; gradients remain enabled.
            scores=model(tokens[:,:-1])
            loss,count,total=sequence_unlikelihood(scores,tokens,prefix.shape[1],window)
            return loss,dict(negativePositions=count,generatedTokens=total,tokens=tokens.detach(),prefixLength=prefix.shape[1])
    finally:
        model.train(was_training)
