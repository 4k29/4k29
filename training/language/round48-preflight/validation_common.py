"""Isolated validation support. Importing this module performs no measurements.

Never restores chunks, edits historical runs, reads DEV/TEST, or promotes weights.
All commands require an externally frozen, SHA-pinned stage-1 receipt.
"""
import argparse
import contextlib
import copy
import hashlib
import importlib.util
import json
import math
import pathlib
import random
import sys

import torch

HERE = pathlib.Path(__file__).resolve().parent
LANG = HERE.parent


def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(pathlib.Path(path).read_text())


def write(path, value):
    pathlib.Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def parser(description):
    p = argparse.ArgumentParser(description=description)
    p.add_argument('--stage1-receipt', type=pathlib.Path, required=True)
    p.add_argument('--stage1-receipt-sha256', required=True)
    p.add_argument('--output', type=pathlib.Path, required=True)
    return p


def gate(args):
    """Receipt is frozen externally after human semantic review, before gradients.

    Schema: manualSemanticPass/allSpeakersAlternate booleans; files maps paths
    relative to HERE to SHA256; includes PREREGISTRATION.json, response-turns.json,
    speaker-audit.json, semantic sample/coverage and all four harness source files.
    The explicit command-line receipt SHA anchors against later self-rebinding.
    """
    if sha(args.stage1_receipt) != args.stage1_receipt_sha256:
        raise ValueError('Frozen stage-1 receipt SHA mismatch')
    receipt = read(args.stage1_receipt)
    if receipt.get('manualSemanticPass') is not True or receipt.get('allSpeakersAlternate') is not True:
        raise ValueError('Stage-1 manual semantic and speaker pass required')
    files = (receipt['files'] if isinstance(receipt['files'], dict) else
             {entry['path']: entry['sha256'] for entry in receipt['files']})
    required = {'PREREGISTRATION.json', 'response-turns.json', 'speaker-audit.json',
                'response_position_ce.py', 'validation_common.py', 'gradient_audit.py',
                'resume_audit.py', 'test_preflight.py'}
    if not required <= set(files):
        raise ValueError('Frozen receipt lacks required inputs/harness files')
    if not any('semantic' in name for name in files) or not any('coverage' in name for name in files):
        raise ValueError('Frozen semantic sample and row coverage receipts required')
    for name, expected in files.items():
        path = (HERE / name).resolve()
        if not path.is_relative_to(HERE) or sha(path) != expected:
            raise ValueError('Frozen stage-1 file changed: ' + name)
    if receipt['featureSha256'] != sha(HERE / 'response-turns.json') or receipt['preregistrationSha256'] != sha(HERE / 'PREREGISTRATION.json'):
        raise ValueError('Frozen receipt feature/preregistration identity differs')
    if receipt['initialCheckpointSha256'] != sha(LANG / 'round47/continue-10000/checkpoint-0.pt'):
        raise ValueError('Frozen receipt initial checkpoint differs')
    prereg = read(HERE / 'PREREGISTRATION.json')
    expected = {'learningRate': 4.4999999999999996e-5, 'sequenceUL': .1,
                'contextCE': .1, 'endEos': .3, 'causalUL': 1.,
                'threads': 2, 'precision': 'float32', 'clipNorm': 1.}
    if prereg['fixedSettings'] != expected:
        raise ValueError('This harness does not match preregistered fixed settings')
    args.output = args.output.resolve()
    if not args.output.is_relative_to(HERE) or args.output.exists():
        raise ValueError('Use a new validation report path inside preflight directory')
    return {'stage1ReceiptSha256': args.stage1_receipt_sha256, 'files': files}


@contextlib.contextmanager
def historical_imports():
    """Temporarily resolve ORIGINAL R46 imports; restore interpreter import globals."""
    names = ['model', 'batching', 'initialization', 'objective', 'sequence_objective',
             'rollout_trace', 'prefix_selection', 'utterance_end_objective',
             'end_main_ce', 'context_preference']
    previous = {name: sys.modules.get(name) for name in names}
    old_path = sys.path[:]
    try:
        for name in names:
            sys.modules.pop(name, None)
        sys.path[:0] = [str(LANG / 'round46'), str(LANG)]
        spec = importlib.util.spec_from_file_location('_round46_preflight_reference', LANG / 'round46/train.py')
        baseline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        yield baseline
    finally:
        sys.path[:] = old_path
        for name, previous_module in previous.items():
            if previous_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous_module


def exact(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b)
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return type(a) is type(b) and len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b


def assert_exact(a, b, label):
    if not exact(a, b):
        raise AssertionError('Bitwise mismatch: ' + label)


def tensor_digest(value):
    h = hashlib.sha256()
    def visit(v):
        if isinstance(v, torch.Tensor):
            t = v.detach().cpu().contiguous()
            h.update(str((str(t.dtype), tuple(t.shape))).encode())
            h.update(t.numpy().tobytes())
        elif isinstance(v, dict):
            for k in sorted(v, key=str):
                h.update(repr(k).encode()); visit(v[k])
        elif isinstance(v, (list, tuple)):
            h.update(type(v).__name__.encode())
            for item in v: visit(item)
        else: h.update(repr(v).encode())
    visit(value)
    return h.hexdigest()


class Runtime:
    def __init__(self):
        self.root = LANG / 'round46'
        self.policy = read(self.root / 'policy.json')
        # Refuse historical source drift against its already-frozen policy.
        for name, expected in self.policy['codeHashes'].items():
            if sha(self.root / name) != expected:
                raise ValueError('Frozen R46 code changed: ' + name)
        for name, expected in self.policy['sourceHashes'].items():
            if sha(LANG / 'round10' / name) != expected:
                raise ValueError('Frozen R46 ancestor source changed: ' + name)
        # Imports do not execute historical main() and module/import globals are restored.
        with historical_imports() as baseline:
            self.b = baseline
        from response_position_ce import Turn, build_weights, position_weighted_main_ce
        self.build_weights = build_weights
        self.weighted_ce = position_weighted_main_ce
        for key, expected in [('learningRate', 4.4999999999999996e-5)]:
            if self.policy[key] != expected: raise ValueError('R46 setting differs: ' + key)
        if self.policy['sequenceUnlikelihood']['coefficient'] != .1 or self.policy['contextPreference']['coefficient'] != .1:
            raise ValueError('R46 auxiliary coefficients differ')
        cp47 = LANG / 'round47/continue-10000/checkpoint-0.pt'
        cp46 = self.root / 'continue-10000/checkpoint-0.pt'
        # Require materialized files. Never invoke restore or download.
        for path in [cp47, cp46]:
            chunk = read(path.with_name(path.name + '.chunks.json'))
            if sha(path) != chunk['sha256']: raise ValueError('Initial checkpoint SHA mismatch')
        self.initial = torch.load(cp47, map_location='cpu', weights_only=False)
        reference = torch.load(cp46, map_location='cpu', weights_only=False)
        for key in ['config', 'model', 'optimizer', 'torchRng', 'pythonRng']:
            assert_exact(self.initial[key], reference[key], 'R47/R46 CP0 ' + key)
        if self.initial['step'] != 0 or reference['step'] != 0:
            raise ValueError('Initial snapshots must be trial step0')
        self.info, self.values = self.b.load_partition(self.root / 'multiview', 'train')
        tok_path = self.root / 'multiview/tokenizer.json'
        self.tok = read(tok_path)
        feature_path = HERE / 'response-turns.json'
        feature = read(feature_path)
        for key, expected in [('trainIndexSha256', sha(self.root / 'multiview/train.index.json')),
                              ('trainTokensSha256', sha(self.root / 'multiview/train.tokens.bin')),
                              ('tokenizerSha256', sha(tok_path))]:
            if feature[key] != expected: raise ValueError('Treatment provenance mismatch ' + key)
        self.turns = {key: [Turn(*row[:3]) for row in rows] for key, rows in feature['turnsByUnit'].items()}
        self.selector = self.b.load_selector(self.root / 'human-turn-token-boundaries.json', self.tok, self.info,
            self.policy['humanNegativePrefix']['featureMapSha256'], sha(tok_path),
            sha(self.root / 'multiview/train.index.json'), sha(self.root / 'sources/documents.jsonl'), min_tokens=8, max_tokens=32)
        self.pool = self.b.load_pool(self.root / self.policy['contextPreference']['pool'], self.policy['contextPreference']['poolSha256'])
        self.strata, self.stratum_weights, self.bucket_masses = self.b.sampler(self.info['rows'], self.policy['genreSampling'])
        pieces = [bytes.fromhex(s) for s in self.tok['bytes']]
        self.clean = [i == 1 or (i >= 6 and bool(p) and not 0x80 <= p[0] < 0xc0) for i, p in enumerate(pieces)]
        loaded = [self.root / 'train.py', LANG / 'model.py'] + [self.root / (name + '.py') for name in
            ['batching', 'initialization', 'objective', 'sequence_objective', 'rollout_trace',
             'prefix_selection', 'utterance_end_objective', 'end_main_ce', 'context_preference']]
        loaded += [cp47, cp46, self.root / 'policy.json', tok_path,
                   self.root / 'multiview/train.index.json', self.root / 'multiview/train.tokens.bin',
                   feature_path, self.root / self.policy['contextPreference']['pool'],
                   self.root / 'human-turn-token-boundaries.json']
        self.receipts = {str(p.relative_to(LANG)): sha(p) for p in loaded}

    def new(self):
        model = self.b.Decoder(copy.deepcopy(self.initial['config']))
        model.load_state_dict(self.initial['model'])
        optimizer = torch.optim.AdamW(model.parameters(), lr=4.4999999999999996e-5, weight_decay=.05)
        optimizer.load_state_dict(copy.deepcopy(self.initial['optimizer']))
        for group in optimizer.param_groups: group['lr'] = 4.4999999999999996e-5
        rng = random.Random(); rng.setstate(self.initial['pythonRng'])
        torch.set_rng_state(self.initial['torchRng'].clone())
        return model, optimizer, rng

    def draw(self, rng):
        return self.b.draw(rng, 8, self.strata, self.stratum_weights, self.bucket_masses)

    def batch(self, width, rows):
        x, y = self.b.pack(rows, self.values, width)
        end = self.b.eligible_mask(rows, y, self.selector.ends, newline_id=16)
        annotated = [dict(row, cleanCharacterStart=self.clean[int(x[i, 0])]) for i, row in enumerate(rows)]
        before = torch.get_rng_state().clone()
        weights, audits = self.build_weights(annotated, y, end, self.turns)
        assert_exact(before, torch.get_rng_state(), 'weight builder RNG')
        return x, y, end, weights, audits

    def objective(self, model, rows, batch, nominal_step, treatment=False, disabled=False, logit_check=False):
        """Use original R46 functions; only the main-CE treatment is new."""
        x, y, end, weights, audits = batch
        model.train()
        logits = model(x)
        ce, original, removed = self.b.main_ce_without_end_newline(logits, y, end)
        main = self.weighted_ce(logits, y, end, weights) if treatment and not disabled else ce
        ul, candidates = self.b.causal_unlikelihood(logits, x, y, window=64)
        eos = self.b.end_eos_loss(logits, y, end, eos_id=2)
        # Absent scheduled terms are graph-connected zeros, matching zero contribution.
        sequence = main * 0; context = main * 0
        sequence_record = None; context_record = None
        if nominal_step % 10 == 0:
            n = self.selector.length(rows[0], int(x[0, 0]))
            sequence, sequence_record = self.b.rollout_unlikelihood(model, x[:1, :n], max_new_tokens=64, eos=2, window=64)
            context, context_record = self.b.preference_loss(model, self.pool, nominal_step // 10 - 1, batch=2)
        components = {'mainCE': main, 'causalUL': ul, 'endEOS': .3 * eos,
                      'sequenceUL': .1 * sequence, 'contextCE': .1 * context}
        # Preserve the original trainer's exact floating-point addition order.
        total = main + 1.0 * ul + .3 * eos
        if nominal_step % 10 == 0:
            total = total + .1 * sequence
            total = total + .1 * context
        logit_reference = None
        scalar_reference_pass = None
        scalar_reference_loss = None
        scalar_absolute_error = None
        if logit_check and treatment and not disabled:
            # Independent reduction (not baseline+delta) against detached logits.
            independent = logits.detach().clone().requires_grad_()
            valid = y.ne(-100)
            raw = torch.nn.functional.cross_entropy(independent.reshape(-1, independent.shape[-1]), y.reshape(-1), reduction='none').reshape_as(y)
            reference = (raw * weights.float()).sum() / valid.sum()
            actual_grad = torch.autograd.grad(main, logits, retain_graph=True)[0]
            reference_grad = torch.autograd.grad(reference, independent)[0]
            logit_reference = bool(torch.allclose(actual_grad, reference_grad, atol=1e-7, rtol=1e-6))
            scalar_reference_pass = bool(torch.allclose(main.detach(), reference.detach(), atol=1e-7, rtol=1e-6))
            scalar_reference_loss = float(reference.detach())
            scalar_absolute_error = float((main.detach()-reference.detach()).abs())
        record = {'nominalStep': nominal_step, 'rowIdentities': [{k: r[k] for k in ['unit', 'start', 'length', 'prefixLength']} for r in rows],
                  'weightAudits': audits, 'components': {k: float(v.detach()) for k, v in components.items()},
                  'totalLoss': float(total.detach()), 'originalCE': float(original.detach()), 'removedCE': float(removed.detach()),
                  'negativeCandidates': candidates, 'sequence': plain(sequence_record), 'context': context_record,
                  'logitsDigest': tensor_digest(logits), 'inputsDigest': tensor_digest((x, y, end)),
                  'independentLogitGradientReferencePass': logit_reference,
                  'independentWeightedCeScalarReferencePass': scalar_reference_pass,
                  'independentWeightedCeScalarReferenceLoss': scalar_reference_loss,
                  'independentWeightedCeScalarAbsoluteError': scalar_absolute_error}
        return total, components, record


def plain(value):
    if isinstance(value, torch.Tensor): return value.detach().cpu().tolist()
    if isinstance(value, dict): return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [plain(v) for v in value]
    return value


def gradient_vector(grads):
    return torch.cat([g.detach().reshape(-1) for g in grads if g is not None])


def gradient_stats(vector, reference=None):
    norm = float(torch.linalg.vector_norm(vector.double()))
    result = {'norm': norm, 'finite': bool(torch.isfinite(vector).all())}
    if reference is not None:
        other = float(torch.linalg.vector_norm(reference.double()))
        result['normRatio'] = norm / other if other else (1. if norm == 0 else None)
        result['cosine'] = float(torch.nn.functional.cosine_similarity(vector.double(), reference.double(), dim=0))
    return result


def configure():
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    torch.set_default_dtype(torch.float32)
