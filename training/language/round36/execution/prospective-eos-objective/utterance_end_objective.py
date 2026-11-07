"""UNTRAINED candidate objective. No import or use by running Round34."""
import bisect
import torch
from torch.nn import functional as F

def eligible_mask(rows, targets, boundaries, newline_id=16):
    if targets.ndim != 2 or len(rows) != targets.shape[0]:
        raise ValueError('Batch and target shapes differ')
    mask = torch.zeros_like(targets, dtype=torch.bool)
    for i, row in enumerate(rows):
        if row['site'] != 'human-chat':
            continue
        ends = boundaries[row['unit']]
        lower = row['start'] + row['prefixLength'] + 1
        upper = row['start'] + row['length']
        for end in ends[bisect.bisect_left(ends, lower):bisect.bisect_right(ends, upper)]:
            t = end - row['start'] - 2
            if not row['prefixLength'] - 1 <= t < row['length'] - 1 or t >= targets.shape[1]:
                raise ValueError('Boundary outside original target interval')
            if int(targets[i, t]) == newline_id:
                mask[i, t] = True
    if (mask & targets.eq(-100)).any():
        raise ValueError('Auxiliary target cannot use an original masked position')
    return mask

def end_eos_loss(logits, targets, mask, eos_id=2):
    if logits.shape[:-1] != targets.shape or mask.shape != targets.shape or mask.dtype != torch.bool:
        raise ValueError('Objective shapes differ')
    if (mask & targets.eq(-100)).any():
        raise ValueError('Masked original targets are ineligible')
    if not mask.any():
        return logits.sum() * 0
    return -F.log_softmax(logits[mask], dim=-1)[:, eos_id].sum() / targets.ne(-100).sum().clamp_min(1)
