"""Recompute the frozen preflight decision; never launch training or alter inputs."""
import hashlib
import json
import pathlib

R = pathlib.Path(__file__).resolve().parent
read = lambda name: json.loads((R / name).read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def assess():
    p = read('PREREGISTRATION.json')
    s = read('stage1-receipt.json')
    g = read('gradient-report.json')
    v = read('resume-report.json')
    integrity = read('original-input-integrity.json')
    failures = []
    for name, digest in s['files'].items():
        if sha(R / name) != digest:
            failures.append('frozen-input-changed:' + name)
    if not (s['manualSemanticPass'] and s['allSpeakersAlternate'] and s['stage1Passed']):
        failures.append('stage1')
    if not integrity['all433OriginalInputsUnmodified']:
        failures.append('original-input-integrity')
    if not g.get('gradientStageComplete') or g.get('ordinaryBatches') != 64 or g.get('stressBatches') != 6:
        failures.append('incomplete-gradient-panel')
    if g.get('actualDisposableOptimizerUpdates') != 0:
        failures.append('unexpected-gradient-stage-updates')
    if g.get('gradientStagePassed') is not True:
        failures.append('gradient-stage-failed')
    failures += ['gradient:' + x['screen'] for x in g.get('failedScreens', [])]
    screens = p['prospectiveOperationalScreens']
    variance = g.get('ordinaryVectorGradientVarianceRatio')
    if variance is None or variance > screens['ordinaryBatchGradientVarianceRatioMaximum']:
        failures.append('independent-vector-variance-screen')
    clipping = g.get('ordinaryClippingIncidenceIncreasePercentagePoints')
    if clipping is None or clipping > screens['ordinaryClippingIncidenceIncreaseMaximumPercentagePoints']:
        failures.append('independent-clipping-screen')
    if g.get('allNoOpAndFallbackBitwiseChecksPass') is not True:
        failures.append('no-op-or-fallback-stage')
    if not all(x['available'] for x in g.get('humanFallbackPanelAvailability', [])):
        failures.append('human-fallback-panel-unavailable')
    low, high = p['prospectiveOperationalScreens']['totalGradientNormRatioInterval']
    for row in g.get('batches', []):
        ratio = row['pairedTotalGradient']['normRatio']
        if ratio is None or not low <= ratio <= high:
            failures.append('independent-gradient-ratio:' + str(row['nominalStep']))
        if not row['noOpBitwisePass']:
            failures.append('no-op:' + str(row['nominalStep']))
        if row['actualWholeBatchFallback'] and row['fallbackBitwisePass'] is not True:
            failures.append('fallback:' + str(row['nominalStep']))
        for name in ['causalUL', 'endEOS', 'sequenceUL', 'contextCE']:
            a = row['baseline']['componentsGradient'][name]
            b = row['treatment']['componentsGradient'][name]
            if a['gradientDigest'] != b['gradientDigest']:
                failures.append('auxiliary-gradient:' + name)
        for label in ['baseline', 'treatment']:
            if not row[label]['allFinite']:
                failures.append('nonfinite:' + label)
        if row['treatment']['independentWeightedCeScalarReferencePass'] is not True:
            failures.append('scalar-reference')
        if row['treatment']['independentLogitGradientReferencePass'] is not True:
            failures.append('gradient-reference')
    if not v.get('resumePassed') or v.get('actualDisposableOptimizerUpdates') != 16:
        failures.append('resume-or-validation-update-count')
    if len(v.get('conditions', [])) != 2 or not all(x['fullStateAndTracesBitwiseEqual'] for x in v.get('conditions', [])):
        failures.append('resume-bitwise-states')
    if any(x['finalAdamCounters'] != [20004] for x in v.get('conditions', [])):
        failures.append('validation-Adam-counter')
    if any(x.get('actualRound48TrainingUpdates') != 0 for x in [g, v]):
        failures.append('unexpected-Round48-training')
    if v.get('gradientReportSha256') != sha(R / 'gradient-report.json'):
        failures.append('gradient-resume-provenance')
    receipt_sha = sha(R / 'stage1-receipt.json')
    if any(x['stage1Receipt']['stage1ReceiptSha256'] != receipt_sha for x in [g, v]):
        failures.append('stage1-provenance')
    out = dict(
        decision='Go' if not failures else 'No-Go',
        scope='Technical preflight only; no Japanese capability improvement established',
        failedChecks=sorted(set(failures)),
        scientificControl='round46', formalAnchor='round25',
        actualRound48TrainingUpdates=0,
        actualDisposableValidationOptimizerUpdates=v.get('actualDisposableOptimizerUpdates'),
        publicModelChanged=False, merged=False, fullTrainingStarted=False,
        stage1ReceiptSha256=receipt_sha,
        gradientReportSha256=sha(R / 'gradient-report.json'),
        resumeReportSha256=sha(R / 'resume-report.json'),
        preregistrationSha256=sha(R / 'PREREGISTRATION.json'),
        limitations=[
            'Adjacent other-speaker next turns; explicit reply-to metadata absent; semantic sample does not certify all pairs',
            'Gradient panel at the aligned initial checkpoint, not all future checkpoints or long-run stability',
            'Four-update resume horizon per path, not a completed production-training run',
            'No new language evaluation or DEV/TEST evaluation during preflight',
            'Passing is not authorization to start training in this task',
        ],
        nextResearchIfFailed='Preserve failed condition and review capacity/data-distribution/objective diagnostics separately; no silent clipping/filter/threshold changes',
    )
    (R / 'decision.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out))


if __name__ == '__main__':
    assess()
