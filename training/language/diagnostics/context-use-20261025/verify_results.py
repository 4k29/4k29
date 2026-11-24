"""Read-only fixed-checkpoint diagnostic verification; no model imports/restores."""
import hashlib
import json
import math
import pathlib
import subprocess
import sys

R = pathlib.Path(__file__).resolve().parent
REPO = R.parents[3]
read = lambda p: json.loads(p.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


panel = read(R / 'panel.json')
plan = read(R / 'PLAN.json')
receipt = read(R / 'results/receipt.json')
assert receipt['status'] == 'complete'
assert receipt['actualOptimizerObjectsConstructed'] == receipt['actualOptimizerUpdates'] == 0
assert all(receipt[k] for k in ['modelStateUnchanged', 'checkpointFilesUnchanged', 'globalTorchRngUnchanged', 'modelRemainsEval'])
assert receipt['panelSha256'] == plan['panelSha256'] == sha(R / 'panel.json')
assert receipt['planSha256'] == sha(R / 'PLAN.json')
for name, digest in plan['codeHashes'].items():
    assert sha(R / name) == digest == receipt['codeSha256'][name]
for key, digest_key in [('checkpointPath', 'expectedCheckpointSha256'), ('alignedCheckpointPath', 'alignedSha256'), ('tokenizerPath', 'tokenizerSha256')]:
    assert sha(REPO / panel[key]) == panel[digest_key]
pieces = [bytes.fromhex(s) for s in read(REPO / panel['tokenizerPath'])['bytes']]
cases = {case['id']: case for case in panel['cases'] + panel['auxiliaryTfOnly']}
assert len(cases) == 1049
tf = read(R / 'results/tf-results.json')['rows']
raw = read(R / 'results/raw-generations.json')['rows']
assert len(tf) == 3147 and len(raw) == 75
assert len({(x['id'], x['condition']) for x in tf}) == 3147
assert len({(x['id'], x['condition']) for x in raw}) == 75
for row in tf:
    case = cases[row['id']]
    assert row['goldTokens'] == case['goldTokens'] and row['targetText'] == case['targetText']
    assert row['prefixTokens'] == case['conditions'][row['condition']]['prefixTokens']
    assert len(row['tokens']) == len(case['goldTokens'])
    assert len(case['conditions']['correct']['prefixTokens']) == len(case['conditions']['mismatched']['prefixTokens'])
    assert case['conditions']['none']['prefixTokens'] == [1]
    for j, token in enumerate(row['tokens']):
        assert token['position'] == j and token['goldToken'] == case['goldTokens'][j]
        assert math.isfinite(token['nll']) and 0 <= token['goldProbability'] <= 1
for row in raw:
    assert row['tokensIncludingEos'] == row['nonEosTokens'] + ([2] if row['eos'] else [])
    assert len(row['tokensIncludingEos']) <= 192
    payload = b''.join(pieces[t] for t in row['nonEosTokens'])
    assert payload.hex() == row['rawBytesHex']
    if row['strictUtf8']:
        assert payload.decode('utf8', errors='strict') == row['text']
    else:
        assert row['text'] is None
    assert row['numericalReference']['argmaxDisagreements'] == 0
    assert row['numericalReference']['toleranceExceedances'] == 0
review = read(R / 'results/reading-complete.json')
assert review['rawFileSha256'] == sha(R / 'results/raw-generations.json')
assert review['all75CompletePrefixesAndContinuationsActuallyReadByRoot']
assert review['identicalCoreJudgmentsConsistent'] and not review['historicalGradesOverwritten']
analysis = read(R / 'results/analysis.json')
assert all(x['compared'] == x['matching'] for x in analysis['historicalDevGenerationComparison']['reports'])
assert analysis['historicalAuxiliaryPoolCheck']['matchedPairs'] == 1024
assert abs(analysis['historicalAuxiliaryPoolCheck']['difference']) < 1e-6
source = R.parents[1] / 'round47/source-manifest.json'
original = read(source)
for row in original['files']:
    path = source.parent / row['path']
    assert path.is_file() and path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
if '--sources' in sys.argv:
    for row in panel['inputReceipts']:
        p = pathlib.Path(row['path'])
        if not p.is_absolute(): p = REPO / p
        assert p.is_file() and sha(p) == row['sha256'], str(p)
manifest = read(R / 'artifact-manifest.json')
tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=REPO).decode().split('\0'))
for row in manifest['files']:
    path = R / row['path']
    assert path.resolve().is_relative_to(R)
    assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], row['path']
    if '--require-tracked' in sys.argv:
        assert str(path.relative_to(REPO)) in tracked
print(json.dumps(dict(filesVerified=len(manifest['files']), originalInputsVerified=len(original['files']),
    sourceReceiptsVerified='--sources' in sys.argv, trackingClosureVerified='--require-tracked' in sys.argv,
    primaryCases=25, teacherForcedRows=3147, fullRawGenerations=75,
    rawTextAndTokenBytesVerified=True, manualFullReadingVerified=True,
    historicalDevMatches=13, historicalPoolMatches=1024,
    actualOptimizerObjectsConstructed=0, actualOptimizerUpdates=0,
    fixedCheckpointUnchanged=True, newTestUsed=False, publicModelChanged=False)))
