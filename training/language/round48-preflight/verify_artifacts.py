"""Read-only hashes/counts/tracking verification. No restores or model execution."""
import hashlib
import json
import pathlib
import subprocess
import sys

R = pathlib.Path(__file__).resolve().parent
REPO = R.parents[2]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


manifest = json.loads((R / 'artifact-manifest.json').read_text())
tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=REPO).decode().split('\0'))
require_tracked = '--require-tracked' in sys.argv
for row in manifest['files']:
    path = R / row['path']
    assert path.resolve().is_relative_to(R)
    assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], row['path']
    if require_tracked:
        assert str(path.relative_to(REPO)) in tracked
original = R.parent / 'round47'
source = json.loads((original / 'source-manifest.json').read_text())
assert sha(original / 'source-manifest.json') == manifest['originalSourceManifestSha256']
for row in source['files']:
    path = original / row['path']
    assert path.is_file() and path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], row['path']
receipt = json.loads((R / 'stage1-receipt.json').read_text())
for name, digest in receipt['files'].items():
    assert sha(R / name) == digest
decision = json.loads((R / 'decision.json').read_text())
resume = json.loads((R / 'resume-report.json').read_text())
gradient = json.loads((R / 'gradient-report.json').read_text())
assert decision['decision'] == manifest['decision'] == 'No-Go'
assert decision['actualRound48TrainingUpdates'] == resume['actualRound48TrainingUpdates'] == gradient['actualRound48TrainingUpdates'] == 0
assert decision['actualDisposableValidationOptimizerUpdates'] == resume['actualDisposableOptimizerUpdates'] == 16
assert resume['resumePassed'] and not gradient['gradientStagePassed']
assert len(gradient['failedScreens']) == 2
assert {(row['nominalStep'], row['screen']) for row in gradient['failedScreens']} == {(39, 'totalGradientNormRatio'), (71, 'totalGradientNormRatio')}
assert gradient['allNoOpAndFallbackBitwiseChecksPass']
print(json.dumps(dict(filesVerified=len(manifest['files']), originalInputsVerified=len(source['files']),
    frozenReceiptVerified=True, trackingClosureVerified=require_tracked,
    actualRound48TrainingUpdates=0, actualDisposableOptimizerUpdates=16,
    fallbackAndResumePass=True, decision='No-Go', trainingStarted=False)))
