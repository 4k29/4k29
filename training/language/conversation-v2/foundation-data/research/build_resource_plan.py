"""Analytical resource estimates only: no model, optimizer, tokenizer fit or TEST."""
import json,pathlib
HERE=pathlib.Path(__file__).resolve().parent

def config(name,vocabulary,context,dim,heads=4):
    layers=8;hidden=4*dim
    parameters=(vocabulary+context)*dim+layers*(12*dim*dim+13*dim)+2*dim
    batch=4
    return dict(name=name,vocabulary=vocabulary,context=context,dim=dim,heads=heads,layers=layers,hidden=hidden,
        parameters=parameters,fp32WeightGradientAdamBytes=16*parameters,
        fullCheckpointApproxBytes=12*parameters,
        forwardLogitsFp32Bytes=batch*context*vocabulary*4,
        materializedAttentionMatricesFp32Bytes=layers*batch*heads*context*context*4,
        illustrativeSavedActivationBytes=layers*batch*context*dim*18*4,
        activationEstimateIsNotPeakMeasurement=True)

def main():
    configs=[config('current-medium',3997,256,320),config('own-bpe-8k',8192,256,320),
        config('own-bpe-16k',16384,256,320),config('context512-only',3997,512,320),
        config('context1024-only',3997,1024,320),config('width512-context512',3997,512,512,8)]
    assert configs[0]['parameters']==11225280
    rates=[1133,5000,20000]
    budgets=[2097152,10000000,30000000,100000000,200000000]
    times=[dict(targetTokens=t,hoursAtRate={str(rate):t/rate/3600 for rate in rates},
        cpu1133IsPriorMeasuredApproximation=True,gpu5000And20000AreUnmeasuredAssumptions=True)for t in budgets]
    result=dict(scope='Planning arithmetic; zero model constructions or optimizer updates',
        formula='N=(V+S)*d+L*(12*d*d+13*d)+2*d; tied token head, hidden4d, all biases and LayerNorm parameters',
        fp32StaticRule='16N bytes: weight4N + gradient4N + two Adam moments8N; excludes activation/runtime',
        checkpointRule='12N bytes plus RNG/order/history/metadata and atomic-save reserve',
        activationRule='18*L*B*S*d*4 illustrative saved activations; not exact autograd peak or VRAM guarantee',
        attentionRule='L*B*H*S^2*4 if materialized; fused SDPA may avoid this allocation; backend unprofiled',
        measuredEnvironment=dict(cpuQuotaCores=2,ramLimitBytes=8589934592,gpuCount=0,
            previousMediumMaximumRssKiB=974316,
            measuredGpuThroughput=None,measuredGpuPeakVram=None,cudaAmpTrainingValidated=False),
        configs=configs,timeScenarios=times,
        suggestedGpuProfile=dict(currentMedium='8–16GiB candidate, small batch first; not a measured minimum',
            largerWidth='12–24GiB candidate; exact peak depends on batch/context/backend/precision'),
        storagePlanning=dict(uint32Tokens10MBytes=40000000,uint32Tokens30MBytes=120000000,
            uint32Tokens100MBytes=400000000,boundedCorpusPilotAdditionalDurableGiB='5–10 operational planning allowance',
            scalableCorpusAndCheckpointWorkspaceGiB='50–100 planning allowance, not mathematical minimum',
            tmpfsIsNotDurableStorage=True),optimizerUpdates=0,sealedTestRead=False)
    (HERE/'RESOURCE_PLAN.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(configs=len(configs),parametersCurrent=configs[0]['parameters'],optimizerUpdates=0)))

if __name__=='__main__':main()
