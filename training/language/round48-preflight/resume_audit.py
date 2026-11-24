"""Sixteen isolated disposable validation updates; never Round48 training.

Requires a completed zero-update gradient report, including failed screens.
An operational-screen failure remains No-Go even if this resume check passes.
"""
import copy
import pathlib
import tempfile

import torch

from validation_common import (HERE, Runtime, assert_exact, configure, gate, parser,
                               read, sha, tensor_digest, write)


NOMINAL_STEPS = (9, 10, 11, 12)


def snapshot(model, optimizer, rng, traces, completed):
    return copy.deepcopy({'schemaVersion': 1,
        'scope': 'Disposable preflight validation only; excluded from Round48 lineage',
        'completedValidationUpdates': completed,
        'lastNominalAuxiliaryScheduleLabel': NOMINAL_STEPS[completed-1] if completed else None,
        'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
        'torchRng': torch.get_rng_state(), 'pythonRng': rng.getstate(),
        'traces': traces, 'modelTraining': model.training})


def update(rt, model, optimizer, rng, nominal, completed, treatment, counter):
    width, rows = rt.draw(rng)
    batch = rt.batch(width, rows)
    optimizer.zero_grad(set_to_none=True)
    for group in optimizer.param_groups:
        if group['lr'] != 4.4999999999999996e-5:
            raise AssertionError('Validation LR changed')
    total, _, record = rt.objective(model, rows, batch, nominal, treatment)
    if not bool(torch.isfinite(total)):
        raise ValueError('Nonfinite validation objective; no optimizer step performed')
    total.backward()
    params = list(model.parameters())
    if any(p.grad is None or not bool(torch.isfinite(p.grad).all()) for p in params):
        raise ValueError('Missing/nonfinite validation gradient; no optimizer step performed')
    norm = torch.nn.utils.clip_grad_norm_(params, 1., error_if_nonfinite=True)
    optimizer.step()
    counter['completedDisposableOptimizerUpdates'] += 1
    if any(not bool(torch.isfinite(p).all()) for p in params):
        raise ValueError('Nonfinite validation parameters')
    record.update(completedValidationUpdates=completed,
                  nominalScheduleLabelIsNotCompletedUpdates=True,
                  preclipGradientNorm=float(norm),
                  modelDigest=tensor_digest(model.state_dict()),
                  optimizerDigest=tensor_digest(optimizer.state_dict()),
                  torchRngDigest=tensor_digest(torch.get_rng_state()),
                  privatePythonRngDigest=tensor_digest(rng.getstate()))
    return record


def trajectory(rt, treatment, split, temporary, counter):
    model, optimizer, rng = rt.new()
    traces = []
    mid_receipt = None
    for completed, nominal in enumerate(NOMINAL_STEPS, 1):
        traces.append(update(rt, model, optimizer, rng, nominal, completed, treatment, counter))
        if split and completed == 2:
            path = pathlib.Path(temporary) / ('treatment' if treatment else 'baseline') / 'midpoint.pt'
            path.parent.mkdir()
            saved = snapshot(model, optimizer, rng, traces, completed)
            torch.save(saved, path)
            mid_receipt = {'sha256': sha(path), 'bytes': path.stat().st_size,
                           'completedValidationUpdates': 2, 'lastNominalAuxiliaryScheduleLabel': 10,
                           'rawDeletedAtEnd': True, 'promotedToExperimentOrPublicModel': False}
            # Actually recreate objects, deserialize disk state, then restore all RNG.
            del model, optimizer, rng, saved
            model, optimizer, rng = rt.new()
            loaded = torch.load(path, map_location='cpu', weights_only=False)
            if loaded['completedValidationUpdates'] != 2:
                raise AssertionError('Wrong validation resume counter')
            model.load_state_dict(loaded['model'])
            optimizer.load_state_dict(loaded['optimizer'])
            rng.setstate(loaded['pythonRng'])
            torch.set_rng_state(loaded['torchRng'])
            model.train(loaded['modelTraining'])
            traces = loaded['traces']
            assert_exact(snapshot(model, optimizer, rng, traces, completed), loaded, 'disk reload full validation state')
    return snapshot(model, optimizer, rng, traces, 4), mid_receipt


def run(args):
    receipt = gate(args)
    if sha(args.gradient_report) != args.gradient_report_sha256:
        raise ValueError('Gradient report SHA mismatch')
    gradient = read(args.gradient_report)
    if gradient.get('gradientStageComplete') is not True or gradient.get('ordinaryBatches') != 64 or gradient.get('stressBatches') != 6 or gradient.get('actualDisposableOptimizerUpdates') != 0:
        raise ValueError('Completed preregistered gradient stage required before resume validation')
    if gradient['stage1Receipt']['stage1ReceiptSha256'] != args.stage1_receipt_sha256:
        raise ValueError('Gradient stage used a different frozen stage1 receipt')
    configure()
    rt = Runtime()
    if gradient['historicalAndInputReceipts'] != rt.receipts:
        raise ValueError('Inputs changed since gradient stage')
    counter = {'completedDisposableOptimizerUpdates': 0}
    report = {'scope': 'Isolated disposable resume validation; no Round48 training or weight promotion',
              'stage1Receipt': receipt, 'historicalAndInputReceipts': rt.receipts,
              'gradientReportSha256': args.gradient_report_sha256,
              'gradientStagePassed': gradient['gradientStagePassed'],
              'inheritedGradientFailedScreens': gradient['failedScreens'],
              'nominalAuxiliaryScheduleLabels': list(NOMINAL_STEPS),
              'actualValidationUpdatesPerTrajectory': 4,
              'plannedDisposableOptimizerUpdates': 16, 'actualRound48TrainingUpdates': 0,
              'noValidationWeightsPromoted': True, 'conditions': [], 'resumePassed': False,
              'fullTrainingGo': False}
    try:
        disposable = HERE / 'disposable'
        disposable.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='resume-', dir=disposable) as temporary:
            for treatment in (False, True):
                uninterrupted, _ = trajectory(rt, treatment, False, temporary, counter)
                resumed, mid = trajectory(rt, treatment, True, temporary, counter)
                for key in ['model', 'optimizer', 'torchRng', 'pythonRng', 'traces',
                            'completedValidationUpdates', 'modelTraining']:
                    assert_exact(uninterrupted[key], resumed[key], 'resumed/uninterrupted ' + key)
                counters = sorted({int(v['step']) for v in resumed['optimizer']['state'].values()})
                report['conditions'].append({'condition': 'treatment' if treatment else 'baseline',
                    'completedValidationUpdatesPerPath': 4, 'executedDisposableOptimizerUpdates': 8,
                    'finalAdamCounters': counters, 'fullStateAndTracesBitwiseEqual': True,
                    'finalStateDigest': tensor_digest(resumed), 'midpointReceipt': mid,
                    'traces': resumed['traces']})
        if counter['completedDisposableOptimizerUpdates'] != 16:
            raise AssertionError('Disposable update accounting differs')
        report['resumePassed'] = True
    except Exception as error:
        report['failure'] = {'type': type(error).__name__, 'message': str(error)}
        raise
    finally:
        report['actualDisposableOptimizerUpdates'] = counter['completedDisposableOptimizerUpdates']
        write(args.output, report)
    return True


if __name__ == '__main__':
    p = parser(__doc__)
    p.add_argument('--gradient-report', type=pathlib.Path, required=True)
    p.add_argument('--gradient-report-sha256', required=True)
    raise SystemExit(0 if run(p.parse_args()) else 2)
