"""Own fresh-model causal training utilities; no pretrained assets or API calls."""
import copy
import hashlib
import importlib.util
import math
import pathlib
import random

import numpy as np
import torch
from torch.nn import functional as F

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]


def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    h = hashlib.sha256()
    def visit(x):
        if isinstance(x, torch.Tensor):
            t = x.detach().cpu().contiguous()
            h.update(str((str(t.dtype), tuple(t.shape))).encode())
            h.update(t.numpy().tobytes())
        elif isinstance(x, dict):
            for k in sorted(x, key=str):
                h.update(repr(k).encode()); visit(x[k])
        elif isinstance(x, (list, tuple)):
            h.update(type(x).__name__.encode())
            for y in x: visit(y)
        else:
            h.update(repr(x).encode())
    visit(value)
    return h.hexdigest()


def exact(a, b):
    if type(a) is not type(b): return False
    if isinstance(a, torch.Tensor):
        return a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b)
    if isinstance(a, dict): return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)): return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b


def decoder(config):
    spec = importlib.util.spec_from_file_location('_conversation_v2_own_decoder', REPO/'training/language/model.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.Decoder(config)


def initialize(config, settings):
    torch.manual_seed(settings['seed'])
    model = decoder(config)
    optimizer = torch.optim.AdamW(model.parameters(), lr=settings['lr'], betas=(.9, .999), eps=1e-8,
                                  weight_decay=settings['weightDecay'])
    # Width changes the number of initialization draws. Start training dropout
    # from a common seed; width-dependent dropout shapes may consume it differently.
    torch.manual_seed(settings['seed'])
    rng = random.Random(settings['samplerSeed'])
    model.train()
    return model, optimizer, rng


def learning_rate(step, settings):
    warmup = settings['warmup']; total = settings['uniqueUpdates']
    if not 1 <= step <= total: raise ValueError('Step outside preregistered schedule')
    if step <= warmup: return settings['lr'] * step / warmup
    progress = (step - warmup) / (total - warmup)
    return settings['minLr'] + .5 * (settings['lr'] - settings['minLr']) * (1 + math.cos(math.pi * progress))


def open_tokens(data, partition):
    path = (REPO/data[partition+'TokensPath']).resolve()
    if not path.is_relative_to(REPO) or sha(path) != data[partition+'TokensSha256']:
        raise ValueError('Frozen token stream mismatch: '+partition)
    values = np.memmap(path, dtype='<u4', mode='r')
    windows = data[partition+'Windows']
    if not windows: raise ValueError('Empty partition')
    for row in windows:
        if not (0 <= row['offset'] < len(values) and 2 <= row['length'] <= 257 and
                row['offset']+row['length'] <= len(values)):
            raise ValueError('Invalid original window')
    return values, windows


def pack(values, windows, indices, vocabulary, context=256):
    x = torch.zeros((len(indices), context), dtype=torch.long)
    y = torch.full_like(x, -100)
    target_tokens = 0; eos_positions = 0; role_positions = 0
    for i, j in enumerate(indices):
        row = windows[j]
        seq = np.array(values[row['offset']:row['offset']+row['length']], dtype=np.int64, copy=True)
        if bool(((seq < 1) | (seq >= vocabulary)).any()): raise ValueError('Invalid content or PAD in real stream')
        n = len(seq)-1
        if n > context: raise ValueError('Window exceeds fixed context')
        x[i, :n] = torch.from_numpy(seq[:-1]); y[i, :n] = torch.from_numpy(seq[1:])
        target_tokens += n; eos_positions += int((seq[1:] == 2).sum())
        role_positions += int(((seq[1:] == 3) | (seq[1:] == 4)).sum())
    return x, y, dict(targetTokens=target_tokens, eosPositions=eos_positions, rolePositions=role_positions)


def causal_ce(logits, targets):
    active = targets.ne(-100)
    if not bool(active.any()): raise ValueError('No genuine targets')
    if not bool(torch.isfinite(logits).all()): raise ValueError('Nonfinite logits')
    loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), targets.reshape(-1), ignore_index=-100)
    # Independent active-position reduction tests padding and token normalization.
    reference = F.cross_entropy(logits[active], targets[active])
    if not torch.allclose(loss, reference, atol=2e-6, rtol=2e-6):
        raise AssertionError('Causal CE differs from direct genuine-token reference')
    return loss


@torch.no_grad()
def clip_grad_accurate(parameters, max_norm=1.0):
    """Same global-L2 clipping rule with FP64 norm aggregation for both widths.

    Parameters, gradients and optimizer remain FP32. A scalar FP64 reduction
    avoids width-dependent FP32 norm underestimation; its common clipping
    coefficient is rounded once to each gradient's dtype before multiplication.
    """
    gradients = [p.grad for p in parameters if p.grad is not None]
    if not gradients or not math.isfinite(max_norm) or max_norm <= 0:
        raise ValueError('Require finite positive max norm and genuine gradients')
    squares = torch.stack([g.detach().double().square().sum() for g in gradients])
    norm = squares.sum().sqrt()
    if not bool(torch.isfinite(norm)): raise ValueError('Nonfinite global gradient norm')
    coefficient = (max_norm/(norm+1e-6)).clamp(max=1.0)
    for gradient in gradients:
        gradient.mul_(coefficient.to(device=gradient.device, dtype=gradient.dtype))
    return norm


def next_batch(rng, order, cursor, count, batch):
    selected = []
    while len(selected) < batch:
        if cursor >= len(order):
            order = list(range(count)); rng.shuffle(order); cursor = 0
        n = min(batch-len(selected), len(order)-cursor)
        selected.extend(order[cursor:cursor+n]); cursor += n
    return selected, order, cursor


def trajectory(model, optimizer, rng, order, cursor, history, unique):
    return copy.deepcopy(dict(config=model.config, model=model.state_dict(), optimizer=optimizer.state_dict(),
        torchRng=torch.get_rng_state(), pythonRng=rng.getstate(), order=order, cursor=cursor,
        history=history, uniqueUpdates=unique, modelTraining=model.training))


def restore(saved, settings):
    model, optimizer, rng = initialize(saved['config'], settings)
    model.load_state_dict(saved['model']); optimizer.load_state_dict(saved['optimizer'])
    torch.set_rng_state(saved['torchRng']); rng.setstate(saved['pythonRng']); model.train(saved['modelTraining'])
    return model, optimizer, rng
