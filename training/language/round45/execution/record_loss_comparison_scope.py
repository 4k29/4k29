"""Describe objective units without modifying or normalizing recorded losses."""
import pathlib,json
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
read=lambda p:json.loads(p.read_text());new=read(R/'policy.json');old=read(R.parent/'round44/policy.json')
assert old['contextPreference']['coefficient']==.1 and new['contextPreference']['coefficient']==.2
out=dict(control='round44',experiment='round45',controlContextCeCoefficient=.1,newContextCeCoefficient=.2,combinedTrainingLossDirectlyComparable=False,reason='Objective coefficient changed; preserve both raw total losses and do not treat a total-loss delta as language improvement',mainDrawsExpectedExactlyMatched=True,unweightedCrossEntropyAndContextNllComponentsReportedSeparately=True,instantaneousLoggedMinibatchLossNotWholeTrainMean=True,validationIsUnchangedCeOnly=True,humanDevNllAndFullGenerationSeparate=True,noRawLossNormalizationOrOutputRepair=True,additionalOptimizerUpdates=0)
(E/'loss-comparison-scope.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
