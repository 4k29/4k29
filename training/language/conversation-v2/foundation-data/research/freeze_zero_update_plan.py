"""Freeze code, selected TRAIN windows and initial-state identity before auditing."""
import argparse,hashlib,json,pathlib
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parents[1];REPO=HERE.parents[4]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main(a):
    if a.output.exists():raise ValueError('Refuse preregistered-plan overwrite')
    inputs=a.inputs.resolve()
    if not inputs.is_relative_to(REPO):raise ValueError('Audit input snapshot must be reviewable in repository')
    bundle=json.loads(inputs.read_text());checkpoint=BASE/'epoch1/medium/archive/checkpoint.pt.chunks.json'
    source=json.loads(checkpoint.read_text())
    expected='5ad249d2c8d5910090c9baba94f94483e9c037139d15b9c4360fd3e975409544'
    if source['sha256']!=expected:raise ValueError('Wrong own medium3470 source')
    files=[HERE/'zero_update_preflight.py',HERE/'prepare_preflight_inputs.py',HERE/'freeze_zero_update_plan.py',
        BASE/'core.py',BASE/'PLAN.json',REPO/'training/language/model.py']
    plan=dict(status='FROZEN_ZERO_UPDATE_PREFLIGHT_ONLY',zeroUpdateAuditAuthorized=a.authorize_zero_update,
        optimizerUpdatesPermitted=0,trainingAuthorized=False,formalAdoption=False,
        initialModel='own medium3470 full model/Adam/RNG/order/history',
        checkpointManifestPath=str(checkpoint.relative_to(REPO)),checkpointManifestSha256=sha(checkpoint),checkpointSha256=expected,
        tokenizerPath=str((BASE/'data/tokenizer.json').relative_to(REPO)),tokenizerSha256=bundle['tokenizerSha256'],
        inputsPath=str(inputs.relative_to(REPO)),inputsSha256=sha(inputs),
        nativeCandidateManifestSha256=bundle['nativeCandidateManifestSha256'],
        selectedWindows={name:[[w['id']for w in batch]for batch in batches]for name,batches in bundle['conditions'].items()},
        codeReceipts={str(p.relative_to(REPO)):sha(p)for p in files},
        policy=dict(batchesPerCondition=2,conditions=['control','dataadd'],maxForwardBackwardBatches=4,
            batchShape=[4,256],allGenuineTargetsPerBatch=1024,dropoutRngMatchedPerPairedBatch=True,
            proseAuditSourceQuota={'jaquad':2,'jawikibooks':1,'jawikivoyage':1},
            sourceQuotaIsNotTrainingMixture=True,bodyEosRoleDoseNotClaimedMatched=True,
            eosCoverageNotEstablishedByFullWindowAudit=True,cpuThreads=2,precision='FP32 plus original FP64 norm reduction',
            clipMaxNorm=1.,clipEpsilon=1e-6,postclipNormTolerance=2e-5,
            actualOptimizerUpdates=0,optimizerStepMustNotBeCalled=True,
            success='finite loss/gradients, original clipping integrity, exact inherited state restore and unchanged model/Adam/Torch+private RNG/sampler/history/source archive',
            gradientRatioOrCosineIsDescriptiveOnly=True,
            learningGo=False,sealedTestRead=False,sourceAdmissionImplied=False,
            noGenerationOrEvalBasedParameterAdjustment=True))
    a.output.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(planSha256=sha(a.output),zeroUpdateAuditAuthorized=a.authorize_zero_update,optimizerUpdatesPermitted=0)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--authorize-zero-update',action='store_true');main(p.parse_args())
