"""Remove competing original newline CE only at the existing true-end EOS mask."""
import torch
from torch.nn import functional as F
def main_ce_without_end_newline(logits,targets,end_mask,newline_id=16):
    if end_mask.dtype!=torch.bool or end_mask.shape!=targets.shape:raise ValueError('Invalid end mask')
    if bool((end_mask & targets.ne(newline_id)).any()):raise ValueError('Only original standalone-newline targets may be excluded')
    valid=targets.ne(-100).sum()
    if int(valid)==0:raise ValueError('No valid targets')
    original=F.cross_entropy(logits.reshape(-1,logits.shape[-1]),targets.reshape(-1))
    if not bool(end_mask.any()):return original,original,original.new_zeros(())
    removed=F.cross_entropy(logits[end_mask],targets[end_mask],reduction='sum')/valid
    return original-removed,original,removed
