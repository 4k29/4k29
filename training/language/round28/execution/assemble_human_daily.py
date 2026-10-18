"""Pair identical authentic everyday DEV targets; no semantic claim or selection."""
import hashlib, json, math, pathlib
E = pathlib.Path(__file__).resolve().parent
old, new = (json.loads((E / f'daily-human-{n}-likelihood.json').read_text()) for n in ['old', 'new'])
for key in old['identity']:
    if key != 'modelSha256': assert old['identity'][key] == new['identity'][key], key
for key in ['documents', 'windows', 'targetTokensIncludingEos', 'serializedUtf8Bytes']:
    assert old[key] == new[key]
rows = []
for a, b in zip(old['rows'], new['rows'], strict=True):
    for key in ['dialogueId', 'sourceSha256', 'serializedTextSha256', 'serializedUtf8Bytes', 'targetTokensIncludingEos']:
        assert a[key] == b[key]
    assert math.isfinite(a['negativeLogLikelihoodSum']) and math.isfinite(b['negativeLogLikelihoodSum'])
    rows.append(dict(dialogueId=a['dialogueId'], oldLossSum=a['negativeLogLikelihoodSum'], newLossSum=b['negativeLogLikelihoodSum'], newMinusOldLossSum=b['negativeLogLikelihoodSum']-a['negativeLogLikelihoodSum'], serializedUtf8Bytes=a['serializedUtf8Bytes']))
record = dict(partition='additional authentic everyday DEV; NOT TEST', developmentDialogues=99, matchedAllCanonicalTargets=True, oldNllPerSerializedUtf8Byte=old['nllPerSerializedUtf8Byte'], newNllPerSerializedUtf8Byte=new['nllPerSerializedUtf8Byte'], newMinusOldNllPerSerializedUtf8Byte=new['nllPerSerializedUtf8Byte']-old['nllPerSerializedUtf8Byte'], independentlyComparableToOriginalMixedViewNll=False, originalStrictGateChanged=False, usedForCheckpointSelection=False, semanticImprovementEstablishedByThisMetric=False, modelTrainingUpdatesByEvaluation=0, reservedTestRead=False, files={n:hashlib.sha256((E / f'daily-human-{n}-likelihood.json').read_bytes()).hexdigest() for n in ['old', 'new']}, rows=rows)
(E / 'daily-human-likelihood-comparison.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='rows'}))
