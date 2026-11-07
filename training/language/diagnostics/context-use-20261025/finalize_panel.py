"""Apply explicit pre-output manual lexical spans without changing any stimuli."""
import copy
import hashlib
import json
import pathlib

R = pathlib.Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
annotations = json.loads((R / 'content-annotations.json').read_text())
panel_path = R / 'panel.json'
before = sha(panel_path)
assert before == annotations['builderOutputPanelSha256'], 'Start from the unannotated builder output'
panel = json.loads(panel_path.read_text())
original = copy.deepcopy(panel)
by_id = {row['id']: row for row in annotations['rows']}
assert set(by_id) == {row['id'] for row in panel['cases']}
for case in panel['cases']:
    row = by_id[case['id']]
    assert hashlib.sha256(case['targetText'].encode()).hexdigest() == row['targetTextSha256']
    assert not case['contentSpans']
    case['contentSpans'] = row['contentSpans']
    case['genericGoldSurfaceTag'] = row['genericGoldSurfaceTag']
    case['unobservedSpeakerMention'] = row['unobservedSpeakerMention']
check = copy.deepcopy(panel)
for case in check['cases']:
    case['contentSpans'] = []
    del case['genericGoldSurfaceTag'], case['unobservedSpeakerMention']
assert check == original, 'Do not alter targets, contexts, donors, splits or tokens'
panel_path.write_text(json.dumps(panel, ensure_ascii=False, indent=2) + '\n')
receipt = dict(builderOutputPanelSha256=before, finalAnnotatedPanelSha256=sha(panel_path),
    manualAnnotationsSha256=sha(R / 'content-annotations.json'),
    codeSha256=sha(pathlib.Path(__file__)),
    stimuliUnchanged=True, modelOutputsSeen=False, actualOptimizerUpdates=0)
(R / 'panel-finalization.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
