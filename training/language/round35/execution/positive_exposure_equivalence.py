"""Reuse target-byte union only after complete same-parent/draw equality proof."""
import pathlib,json,hashlib,copy
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round34';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=read(E/'paired-training-audit.json');audit=read(E/'optimizer-audit.json');ref=P/'execution/continued-human-exposure-10000.json';old=read(ref)
assert proof['actualUpdatesEach']==audit['actualCompletedUpdates']==10000
assert proof['sameAlignedInitialModelOptimizerAndRng'] and proof['samePositiveSamplerDrawTraceAndAllTargetCounts']
assert old['snapshots']['parentPlusChild']['allTargetTokens']-old['snapshots']['parentActual10000']['allTargetTokens']==audit['seenTargetTokens']
assert old['snapshots']['parentPlusChild']['allTargetBytes']-old['snapshots']['parentActual10000']['allTargetBytes']==audit['seenTargetUtf8Bytes']
out=copy.deepcopy(old);out.update(childCheckpointSha256=audit['checkpointSha256'],referenceRound34CheckpointSha256=old['childCheckpointSha256'],referenceReportSha256=sha(ref),pairedCompleteDrawEqualityEvidenceSha256=sha(E/'paired-training-audit.json'),sameOriginalPositiveTargetExposureReusedAfterExactProof=True,notNewIndependentExposureMeasurement=True,codeSha256=sha(pathlib.Path(__file__)))
(E/'continued-human-exposure-10000.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(actualChildUpdates=10000,oldCoverage=out['snapshots']['parentActual10000']['uniqueRawByteCoverage'],newCoverage=out['snapshots']['parentPlusChild']['uniqueRawByteCoverage'],notSemanticEvidence=True)))
