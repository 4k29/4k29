"""Retain full raw everyday continuations and numerical evidence; never guess semantics."""
import hashlib, json, pathlib, re
R = pathlib.Path(__file__).resolve().parents[1]
E = R / 'execution'
read = lambda p: json.loads(p.read_text())
old, new = (read(E / f'daily-{name}-python.json') for name in ['old', 'new'])
assert old['probeSha256'] == new['probeSha256'] == hashlib.sha256((E / 'daily-probes.json').read_bytes()).hexdigest()
assert old['maxNewTokens'] == new['maxNewTokens'] == 192
assert old['evaluationThreads'] == new['evaluationThreads'] == 1
assert len(old['rows']) == len(new['rows']) == 12
lines = ['# Everyday Japanese — unabridged additional DEV continuations', '', 'These openings are an exposed development diagnostic, not a new TEST. No target answers, output editing, retrieval, decoding penalties or semantic score inference. All outputs and tokens are retained in the JSON files. No weight selection uses this diagnostic.', '']
for a, b in zip(old['rows'], new['rows'], strict=True):
    assert all(a[k] == b[k] for k in ['id', 'prefix', 'group'])
    fence = '`' * max(3, 1 + max((len(x) for x in re.findall(r'`+', a['prefix']+a['text']+b['text'])), default=0))
    lines += ['## '+a['id'], '', 'Opening:', '', fence+'text', a['prefix'], fence, '', 'Old full continuation:', '', fence+'text', a['text'], fence, '', 'New full continuation:', '', fence+'text', b['text'], fence, '']
(E / 'DAILY_FULL_GENERATIONS.md').write_text('\n'.join(lines)+'\n')
record = dict(developmentOnly=True, newTestUsed=False, usedForWeightSelection=False, semanticAssessment='Pending actual full reading; no semantic grade guessed', originalStrictGateChanged=False, models={})
for name, g in [('old', old), ('new', new)]:
    js = read(E / f'daily-{name}-javascript.json')
    assert js['modelSha256'] == g['modelFileSha256']
    mismatches = [a['id'] for a, b in zip(g['rows'], js['rows'], strict=True) if any(a[k] != b[k] for k in ['id', 'text', 'tokens', 'eos', 'validUtf8', 'validTokens', 'inputTokens'])]
    assert js['completeGenerationParity'] == (not mismatches)
    error = max(x['maxAbsoluteError'] for x in js['references'])
    record['models'][name] = dict(modelSha256=g['modelFileSha256'], generationSha256=hashlib.sha256((E / f'daily-{name}-python.json').read_bytes()).hexdigest(), matchingSequences=12-len(mismatches), mismatches=mismatches, maxReferenceLogitError=error, unchangedReferenceTolerance=2e-4, referenceWithinTolerance=error<=2e-4)
(E / 'daily-numerical-comparison.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(record, ensure_ascii=False))
if any(x['matchingSequences'] != 12 or not x['referenceWithinTolerance'] for x in record['models'].values()):
    raise SystemExit(1)
