"""Preregistered zero-optimizer-update paired real-checkpoint gradient audit."""
import copy
import math
import pathlib
import random

import torch

from validation_common import (HERE, Runtime, assert_exact, configure, exact, gate,
    gradient_stats, gradient_vector, parser, read, tensor_digest, write)


def measure(rt, model, rows, batch, step, treatment, disabled=False):
    model.zero_grad(set_to_none=True)
    total, components, record = rt.objective(model, rows, batch, step, treatment, disabled, logit_check=True)
    params = list(model.parameters())
    component_stats = {}
    component_vectors = {}
    for name, loss in components.items():
        grads = torch.autograd.grad(loss, params, retain_graph=True, allow_unused=True)
        missing = [i for i, g in enumerate(grads) if g is None]
        # All components include a full-model CE/UL graph, including scheduled zeros.
        vector = gradient_vector(grads)
        component_stats[name] = {**gradient_stats(vector), 'missingParameterGradients': missing,
                                 'gradientDigest': tensor_digest(grads)}
        component_vectors[name] = vector
    total.backward()
    gradients = [p.grad for p in params]
    record['missingParameterGradients'] = [i for i, g in enumerate(gradients) if g is None]
    vector = gradient_vector(gradients).clone()
    stats = gradient_stats(vector)
    norm = stats['norm']
    for name, component in component_vectors.items():
        component_stats[name]['relativeNormToTotal'] = component_stats[name]['norm'] / norm if norm else None
        component_stats[name]['cosineToTotal'] = gradient_stats(component, vector)['cosine']
    record['totalGradient'] = stats
    record['componentsGradient'] = component_stats
    record['wouldClipAtOne'] = norm > 1.
    record['gradientDigest'] = tensor_digest(gradients)
    record['torchRngAfterDigest'] = tensor_digest(torch.get_rng_state())
    record['modelTrainingAfter'] = model.training
    record['allFinite'] = (math.isfinite(record['totalLoss']) and stats['finite'] and
        all(math.isfinite(v) for v in record['components'].values()) and
        all(v['finite'] for v in component_stats.values()))
    return vector, record, torch.get_rng_state().clone()


class Moments:
    """Population vector variance, not variance of gradient norms; one running vector."""
    def __init__(self):
        self.n = 0; self.mean = None; self.m2 = 0.; self.norms = []

    def add(self, vector):
        v = vector.double()
        self.n += 1
        self.norms.append(float(torch.linalg.vector_norm(v)))
        if self.mean is None:
            self.mean = v.clone()
        else:
            delta = v - self.mean
            self.mean.add_(delta / self.n)
            self.m2 += float(torch.dot(delta, v-self.mean))

    def result(self):
        mean_norm = sum(self.norms) / self.n
        return {'batches': self.n, 'populationVectorGradientVariance': self.m2 / self.n,
                'populationGradientNormVariance': sum((n-mean_norm)**2 for n in self.norms)/self.n,
                'meanGradientNorm': mean_norm, 'meanGradientVectorNorm': float(torch.linalg.vector_norm(self.mean))}


def stress_batches(rt, frozen_files):
    """Use stage-1 exhaustive coverage's frozen, source/view maximum-weight panel."""
    candidates = [HERE / name for name in frozen_files if 'coverage' in name and name.endswith('.json')]
    for path in candidates:
        coverage = read(path)
        if 'stressBatches' in coverage:
            stress = coverage['stressBatches']
            if len(stress) != 6: raise ValueError('Exactly six stress batches required')
            seen = set()
            for entry in stress:
                source, view = entry['source'], entry['view']
                if (source, view) in seen: raise ValueError('Duplicate stress stratum')
                seen.add((source, view))
                indices = entry['rowIndices']
                if len(indices) != 8 or len(set(indices)) != 8: raise ValueError('Stress must have eight distinct rows')
                rows = [rt.info['rows'][i] for i in indices]
                width = entry['width']
                if any(next(w for w in (64,128,256) if r['length']-1 <= w) != width for r in rows):
                    raise ValueError('Stress width mismatch')
                yield width, rows, {'source': source, 'view': view, 'rowIndices': indices, 'coverageSha256': frozen_files[str(path.relative_to(HERE))]}
            if seen != {(source, view) for source in ['realpersona', 'jmrd'] for view in range(3)}:
                raise ValueError('Stress source/view panel incomplete')
            return
    raise ValueError('Frozen coverage must expose stressBatches source/view/width/rowIndices')


def human_fallback_batches(rt):
    """First eight actual human fallback rows per reason; no model measurements.

    These are invariant-only panels outside ordinary/stress statistics. Do not
    classify unchanged C=S eligible rows as fallback.
    """
    reasons = ('unclean-character-start', 'no-complete-aligned-reply-with-complete-context')
    selected = {reason: [] for reason in reasons}
    indices = {reason: [] for reason in reasons}
    for index, row in enumerate(rt.info['rows']):
        if row['site'] != 'human-chat':
            continue
        width = next(w for w in (64,128,256) if row['length']-1 <= w)
        batch = rt.batch(width, [row])
        audit = batch[4][0]
        reason = audit['fallback']
        if reason in selected and audit['selectedTurn'] is None and len(selected[reason]) < 8:
            assert_exact(batch[3], (batch[1].ne(-100) & ~batch[2]).double(), 'human fallback row weights')
            selected[reason].append(row)
            indices[reason].append(index)
        if all(len(rows) == 8 for rows in selected.values()):
            break
    panels = []
    for reason in reasons:
        rows = selected[reason]
        if not rows:
            panels.append((None, [], {'fallbackReason': reason, 'rowIndices': [],
                'available': False, 'selection': 'No such actual human rows in exhaustive original index scan'}))
            continue
        width = next(w for w in (64,128,256) if max(r['length']-1 for r in rows) <= w)
        panels.append((width, rows, {'fallbackReason': reason, 'rowIndices': indices[reason],
            'available': True, 'selection': 'First up to eight matching original human rows in index order',
            'excludedFromOrdinaryAndStressStatistics': True}))
    return panels


def compare(rt, model, width, rows, step, state, group):
    batch = rt.batch(width, rows)
    original = tensor_digest(batch[:3])
    torch.set_rng_state(state.clone())
    base_vector, baseline, base_after = measure(rt, model, rows, batch, step, False)
    torch.set_rng_state(state.clone())
    vector, treatment, treatment_after = measure(rt, model, rows, batch, step, True)
    assert_exact(base_after, treatment_after, 'paired full-objective Torch RNG')
    if original != tensor_digest(batch[:3]): raise AssertionError('Input/targets/end-mask changed')
    assert_exact(baseline['logitsDigest'], treatment['logitsDigest'], 'paired logits')
    for name in ['causalUL', 'endEOS', 'sequenceUL', 'contextCE']:
        assert_exact(baseline['components'][name], treatment['components'][name], 'unchanged ' + name)
        for key in ['norm', 'finite', 'missingParameterGradients', 'gradientDigest']:
            assert_exact(baseline['componentsGradient'][name][key], treatment['componentsGradient'][name][key], 'unchanged component gradient ' + name + ':' + key)
    # No-op exercises the disabled treatment entry point, with actual total.backward.
    torch.set_rng_state(state.clone())
    no_op_vector, no_op, no_op_after = measure(rt, model, rows, batch, step, True, disabled=True)
    assert_exact(base_vector, no_op_vector, 'disabled treatment parameter gradients')
    assert_exact(base_after, no_op_after, 'disabled treatment RNG')
    for key in ['totalLoss', 'components', 'gradientDigest', 'torchRngAfterDigest', 'modelTrainingAfter']:
        assert_exact(baseline[key], no_op[key], 'disabled treatment ' + key)
    fallback = torch.equal(batch[3], (batch[1].ne(-100) & ~batch[2]).double())
    if fallback:
        assert_exact(base_vector, vector, 'actual fallback parameter gradients')
        assert_exact(baseline['totalLoss'], treatment['totalLoss'], 'actual fallback loss')
    stats = gradient_stats(vector, base_vector)
    ratio = stats['normRatio']
    failed = []
    if ratio is None or not .25 <= ratio <= 4.: failed.append('totalGradientNormRatio')
    for label, record in [('baseline', baseline), ('treatment', treatment), ('disabled', no_op)]:
        if not record['allFinite']: failed.append(label + ':nonfinite')
        if record['missingParameterGradients'] or any(v['missingParameterGradients'] for v in record['componentsGradient'].values()):
            failed.append(label + ':missingGradient')
    if treatment['independentLogitGradientReferencePass'] is not True:
        failed.append('independentLogitGradientReference')
    if treatment['independentWeightedCeScalarReferencePass'] is not True:
        failed.append('independentWeightedCeScalarReference')
    result = {'group': group, 'nominalStep': step, 'baseline': baseline, 'treatment': treatment,
              'pairedTotalGradient': stats, 'noOpBitwisePass': True,
              'actualWholeBatchFallback': fallback, 'fallbackBitwisePass': True if fallback else None,
              'failedScreens': failed}
    # Advance the ordinary dropout stream exactly once, using baseline post-state.
    torch.set_rng_state(base_after)
    return result, base_vector, vector, base_after


def run(args):
    receipt = gate(args)
    configure()
    rt = Runtime()
    model, optimizer, rng = rt.new()
    initial_digest = tensor_digest({'model': model.state_dict(), 'optimizer': optimizer.state_dict()})
    initial_python = rng.getstate()
    state = torch.get_rng_state().clone()
    rows_report = []; failures = []
    moments = {'baseline': Moments(), 'treatment': Moments()}
    # Freeze stress identities before any forward/gradient measurements.
    stresses = list(stress_batches(rt, receipt['files']))
    human_fallbacks = human_fallback_batches(rt)
    for step in range(1,65):
        width, rows = rt.draw(rng)
        row, baseline, treatment, state = compare(rt, model, width, rows, step, state, 'ordinary')
        rows_report.append(row)
        moments['baseline'].add(baseline); moments['treatment'].add(treatment)
        failures.extend({'nominalStep': step, 'screen': name} for name in row['failedScreens'])
        print('ordinary', step, 'complete', flush=True)
    for step, (width, rows, metadata) in zip(range(70,76), stresses):
        row, _, _, state = compare(rt, model, width, rows, step, state, 'stress')
        row['stressMetadata'] = metadata; rows_report.append(row)
        failures.extend({'nominalStep': step, 'screen': name} for name in row['failedScreens'])
        print('stress', step, 'complete', flush=True)
    # Explicit actual ineligible examples ensure fallback equality even if no random
    # ordinary batch happens to consist entirely of fallback rows.
    fallback_rows = [r for r in rt.info['rows'] if r['site'] != 'human-chat'][:8]
    width = next(w for w in (64,128,256) if max(r['length']-1 for r in fallback_rows) <= w)
    row, _, _, state = compare(rt, model, width, fallback_rows, 80, state, 'explicit-actual-fallback')
    if not row['actualWholeBatchFallback']: raise AssertionError('Explicit fallback batch unexpectedly treated')
    rows_report.append(row)
    failures.extend({'nominalStep': 80, 'screen': name} for name in row['failedScreens'])
    fallback_availability = []
    for step, (width, rows, metadata) in zip((81,82), human_fallbacks):
        fallback_availability.append(metadata)
        if not rows:
            continue
        row, _, _, state = compare(rt, model, width, rows, step, state, 'explicit-actual-human-fallback')
        if not row['actualWholeBatchFallback']:
            raise AssertionError('Explicit human fallback unexpectedly treated')
        if any(a['selectedTurn'] is not None or a['fallback'] != metadata['fallbackReason']
               for a in row['treatment']['weightAudits']):
            raise AssertionError('Human fallback reason changed after batching')
        row['fallbackMetadata'] = metadata
        rows_report.append(row)
        failures.extend({'nominalStep': step, 'screen': name} for name in row['failedScreens'])
    statistics = {name: value.result() for name, value in moments.items()}
    old = statistics['baseline']['populationVectorGradientVariance']
    new = statistics['treatment']['populationVectorGradientVariance']
    variance_ratio = new / old if old else (1. if new == 0 else None)
    ordinary = [r for r in rows_report if r['group'] == 'ordinary']
    base_clip = sum(r['baseline']['wouldClipAtOne'] for r in ordinary)/64
    treatment_clip = sum(r['treatment']['wouldClipAtOne'] for r in ordinary)/64
    clipping_increase = 100*(treatment_clip-base_clip)
    if variance_ratio is None or variance_ratio > 16.: failures.append({'screen': 'ordinaryVectorGradientVarianceRatio'})
    if clipping_increase > 25.: failures.append({'screen': 'ordinaryClippingIncidenceIncrease'})
    assert_exact(initial_digest, tensor_digest({'model': model.state_dict(), 'optimizer': optimizer.state_dict()}), 'zero optimizer updates/unchanged state')
    report = {'scope': 'Zero-update preflight; not Round48 training or language capability evidence',
              'actualDisposableOptimizerUpdates': 0, 'actualRound48TrainingUpdates': 0,
              'stage1Receipt': receipt, 'historicalAndInputReceipts': rt.receipts,
              'ordinaryBatches': 64, 'stressBatches': 6,
              'explicitFallbackBatches': 1 + sum(bool(rows) for _, rows, _ in human_fallbacks),
              'humanFallbackPanelAvailability': fallback_availability,
              'fallbackPanelsExcludedFromOrdinaryAndStressStatistics': True,
              'parameterGradientVariance': statistics, 'ordinaryVectorGradientVarianceRatio': variance_ratio,
              'baselineOrdinaryClippingFraction': base_clip, 'treatmentOrdinaryClippingFraction': treatment_clip,
              'ordinaryClippingIncidenceIncreasePercentagePoints': clipping_increase,
              'initialPrivatePythonRngDigest': tensor_digest(initial_python), 'finalPrivatePythonRngDigest': tensor_digest(rng.getstate()),
              'allNoOpAndFallbackBitwiseChecksPass': True, 'failedScreens': failures,
              'gradientStageComplete': True, 'gradientStagePassed': not failures,
              'fullTrainingGo': False, 'batches': rows_report}
    write(args.output, report)
    return not failures


if __name__ == '__main__':
    args = parser(__doc__).parse_args()
    try:
        passed = run(args)
    except Exception as error:
        # Preserve an explicit incomplete report, rather than implying the panel
        # or any Go criterion completed. The caller captures the full traceback.
        if args.output.resolve().is_relative_to(HERE) and not args.output.exists():
            write(args.output, {'scope': 'Preflight failed before completion',
                  'actualDisposableOptimizerUpdates': 0, 'actualRound48TrainingUpdates': 0,
                  'gradientStageComplete': False, 'gradientStagePassed': False,
                  'fullTrainingGo': False,
                  'failure': {'type': type(error).__name__, 'message': str(error)}})
        raise
    raise SystemExit(0 if passed else 2)
