"""TRAIN-only prototype; no repository integration or training performed.

All unit coordinates index the original BOS-containing token stream. A turn's
[start,end) includes its authentic following separator when present, but never
BOS/EOS. Keep EVERY authentic turn in source order, including unaligned turns
whose start or end is None. Never infer adjacency from aligned-only ends.
"""
from dataclasses import dataclass
import hashlib
import torch
from torch.nn import functional as F


@dataclass(frozen=True)
class Turn:
    index: int
    start: int | None
    end: int | None


def build_weights(rows, targets, end_mask, turns_by_unit):
    """Return weights and audits, without forward passes or random draws.

    Main CE positions excluded by the existing true-end newline mask remain
    zero. Human rows with a complete reply and its complete preceding turn
    visible receive their ORIGINAL active-CE mass only on that reply's active
    CONTENT positions. Existing BOS/EOS target weights stay exactly one.
    Other rows/fallbacks retain the exact old per-position weights.
    The CE denominator remains targets.ne(-100).sum(), not weights.nonzero().
    Selection is a fixed SHA-derived uniform-index rule over eligible replies
    within each row (salt r48-response-ce-v1), with no training RNG consumed.
    This is not a claim of corpus-unbiased utterance sampling.
    """
    if targets.ndim != 2 or len(rows) != targets.shape[0]:
        raise ValueError("Row/target shape mismatch")
    if end_mask.dtype != torch.bool or end_mask.shape != targets.shape:
        raise ValueError("End mask must match targets")
    valid = targets.ne(-100)
    if bool((end_mask & (~valid | targets.ne(16))).any()):
        raise ValueError("End exclusion only permits original unmasked newline16")
    active = valid & ~end_mask
    protected = active & (targets.eq(1) | targets.eq(2))
    content = active & ~protected
    weights = active.to(torch.float64)
    audits = []
    for i, row in enumerate(rows):
        original_mass = int(active[i].sum())
        audit = {"originalValidTargets": int(valid[i].sum()),
                 "originalActiveCeTargets": original_mass,
                 "originalContentCeTargets": int(content[i].sum()),
                 "protectedBosEosTargets": int(protected[i].sum()),
                 "eligibleReplies": 0, "selectedTurn": None, "fallback": None,
                 "weightedCeMass": float(original_mass)}
        if row["site"] != "human-chat":
            audit["fallback"] = "nonhuman-unchanged"
            audits.append(audit)
            continue
        # Row starts inside UTF8 characters are legal old byte-BPE training
        # rows; preserve them unchanged rather than pretending full context.
        if not row.get("cleanCharacterStart", False):
            audit["fallback"] = "unclean-character-start"
            audits.append(audit)
            continue
        start, length, prefix = row["start"], row["length"], row["prefixLength"]
        if not (start >= 0 and 1 <= prefix < length <= targets.shape[1]+1):
            raise ValueError("Invalid original row coordinates")
        turns = turns_by_unit[row["unit"]]
        if any(t.index != j for j, t in enumerate(turns)):
            raise ValueError("Feature must retain every authentic turn in order")
        candidates = []
        for j in range(1, len(turns)):
            previous, reply = turns[j-1], turns[j]
            if any(x is None for x in (previous.start, previous.end, reply.start, reply.end)):
                continue
            if not previous.start < previous.end == reply.start < reply.end:
                raise ValueError("Authentic neighboring turns must meet")
            if not (start <= previous.start and start+prefix <= reply.start and reply.end <= start+length):
                continue
            # y[t] corresponds to source token start+t+1.
            lo, hi = reply.start-start-1, reply.end-start-1
            if not (0 <= lo < hi <= targets.shape[1]):
                raise ValueError("Reply outside teacher-forced target coordinates")
            # A complete reply cannot include formerly masked targets.
            if not bool(valid[i, lo:hi].all()):
                continue
            selected = torch.zeros_like(active[i])
            selected[lo:hi] = content[i, lo:hi]
            if bool(selected.any()):
                candidates.append((reply.index, selected))
        audit["eligibleReplies"] = len(candidates)
        if not candidates:
            audit["fallback"] = "no-complete-aligned-reply-with-complete-context"
        else:
            salt = "r48-response-ce-v1"
            key = f"{salt}|{row['unit']}|{start}|{length}|{prefix}".encode()
            bound = (1 << 256) - ((1 << 256) % len(candidates))
            counter = 0
            value = int.from_bytes(hashlib.sha256(key).digest(), "big")
            while value >= bound:
                counter += 1
                value = int.from_bytes(hashlib.sha256(key+f"|{counter}".encode()).digest(), "big")
            k = value % len(candidates)
            turn_index, selected = candidates[k]
            n = int(selected.sum())
            content_mass = int(content[i].sum())
            weights[i, content[i]] = 0
            weights[i, selected] = content_mass/n
            audit["selectedTurn"] = turn_index
            audit["selectedActiveCeTargets"] = n
            audit["positionWeight"] = content_mass/n
        audit["weightedCeMass"] = float(weights[i].sum())
        audits.append(audit)
    return weights, audits


def position_weighted_main_ce(logits, targets, end_mask, weights):
    """FP32 loss reduction; input weights checked against OLD per-row CE mass."""
    if logits.shape[:-1] != targets.shape or weights.shape != targets.shape:
        raise ValueError("Loss shapes differ")
    if end_mask.dtype != torch.bool or end_mask.shape != targets.shape:
        raise ValueError("End mask must match targets")
    valid = targets.ne(-100)
    if bool((end_mask & (~valid | targets.ne(16))).any()):
        raise ValueError("End exclusion only permits original unmasked newline16")
    if not bool(valid.any()):
        raise ValueError("No original valid targets")
    active = valid & ~end_mask
    protected = active & (targets.eq(1) | targets.eq(2))
    if bool((weights[protected] != 1).any()):
        raise ValueError("Original BOS/EOS target weights changed")
    if not bool(torch.isfinite(weights).all()) or bool((weights < 0).any()):
        raise ValueError("Invalid weights")
    if bool((weights[~active] != 0).any()):
        raise ValueError("Weights restore an excluded/masked original position")
    if not torch.allclose(weights.sum(-1).double(), active.sum(-1).double(), atol=1e-9, rtol=1e-9):
        raise ValueError("Original row CE mass changed")
    flat_logits = logits.float().reshape(-1, logits.shape[-1])
    flat_targets = targets.reshape(-1)
    # Preserve the exact old reduction path, adding a delta only for the
    # treatment positions. With no changed weights this is bitwise baseline.
    base = F.cross_entropy(flat_logits, flat_targets)
    if bool(end_mask.any()):
        base = base-F.cross_entropy(logits.float()[end_mask], targets[end_mask], reduction="sum")/valid.sum()
    delta_weights = weights.float()-active.float()
    if not bool(delta_weights.ne(0).any()):
        return base
    ce = F.cross_entropy(flat_logits, flat_targets, reduction="none").reshape_as(targets)
    return base+(ce*delta_weights).sum()/valid.sum()
