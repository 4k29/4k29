"""Auditable process-loss recovery: same first-epoch trajectory, honest work counters."""
import argparse,ast,hashlib,json,pathlib,time
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[3]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text())
def transform(source,model):
    replacements=[("if a.deadline>plan['globalDeadlineUnix']:","if a.deadline>RECOVERY['deadlineUnix']:")]
    if model=='medium':
        replacements += [
          ("pfpath=out/('preflight-v2.json' if a.preflight_only else 'run-zero-update-preflight.json')","pfpath=out/(f'recovery-zero-update-{unique}-{actual}-{time.time_ns()}.json' if a.resume else ('preflight-v2.json' if a.preflight_only else 'run-zero-update-preflight.json'))"),
          ("if actual>=2960:","if actual>=RECOVERY['actualCaps'][a.model]:"),
          ("            update()\n","            update(replay=(unique<RECOVERY['lostThroughUniqueUpdate']))\n")]
    changed=source
    for old,new in replacements:
        if changed.count(old)!=1:raise ValueError('Unexpected original source target count: '+old)
        changed=changed.replace(old,new)
    normalized=changed
    for old,new in reversed(replacements):
        if normalized.count(new)!=1:raise ValueError('Unexpected transformed source target count')
        normalized=normalized.replace(new,old)
    if normalized!=source or ast.dump(ast.parse(normalized))!=ast.dump(ast.parse(source)):raise AssertionError('Additional AST/source changes')
    return changed,dict(exactDeclaredChangesOnly=True,allOtherAstNodesIdentical=True,
        replacements=[dict(old=old,new=new)for old,new in replacements],effectiveSourceSha256=hashlib.sha256(changed.encode()).hexdigest())
def main(a):
    if sha(a.amendment)!=a.amendment_sha:raise ValueError('Recovery amendment SHA mismatch')
    amendment=read(a.amendment)
    for p,h in amendment['codeAndInputReceipts'].items():
        if sha(REPO/p)!=h:raise ValueError('Frozen recovery input changed: '+p)
    if sha(a.plan)!=amendment['originalPlanSha256'] or a.plan_sha!=amendment['originalPlanSha256']:raise ValueError('Wrong original plan')
    if a.deadline!=amendment['deadlineUnix']:raise ValueError('Wrong declared no-clock-cap sentinel')
    sourcepath=HERE/'continue_train.py';changed,audit=transform(sourcepath.read_text(),a.model)
    if audit['effectiveSourceSha256']!=amendment['effectiveSourceSha256'][a.model]:raise ValueError('Wrong effective code')
    environment={'__file__':str(sourcepath),'__name__':'_epoch1_explicit_process_loss_recovery','RECOVERY':amendment}
    exec(compile(changed,str(sourcepath),'exec'),environment)
    environment['torch'].set_num_threads(2);environment['torch'].use_deterministic_algorithms(True)
    original_loader=environment['load_chunks'];state_metadata_audit=None
    def migrated_loader(manifest):
        nonlocal state_metadata_audit
        value=original_loader(manifest)
        if a.model!='medium':return value
        if read(manifest)['sha256']!=amendment['recoveryFromCheckpointSha256']:raise ValueError('Recovery must start from preserved known state2560')
        if value['actualContinuationUpdates']!=2050 or value['trajectory']['uniqueUpdates']!=2560:raise ValueError('Wrong durable work counters')
        if value['deadline']!=amendment['originalDeadlineUnix']:raise ValueError('Unexpected checkpoint deadline')
        before=environment['digest'](value['trajectory']);copied=dict(value)
        copied['actualContinuationUpdates']=amendment['alreadyCompletedActualUpdates'];copied['deadline']=a.deadline
        after=environment['digest'](copied['trajectory'])
        if before!=after:raise AssertionError('Metadata migration changed model/Adam/RNG/history/order')
        state_metadata_audit=dict(beforeTrajectoryDigest=before,afterTrajectoryDigest=after,allTrajectoryFieldsUnchanged=True,
            originalActualContinuationUpdates=value['actualContinuationUpdates'],migratedActualContinuationUpdates=copied['actualContinuationUpdates'],
            actualCompletedButNotDurableUpdates=92,originalDeadline=value['deadline'],newDeadline=a.deadline,
            unavailableLostStateBitwiseComparison=True,originalStoredCheckpointUnmodified=True)
        return copied
    environment['load_chunks']=migrated_loader
    a.resume=a.model=='medium'
    if a.model=='medium':
        checkpoint=pathlib.Path(amendment['rollingCheckpointManifest']);ledger=HERE/'medium/optimizer-ledger.jsonl'
        if read(checkpoint)['sha256']!=amendment['recoveryFromCheckpointSha256'] or sha(ledger)!=amendment['interruptedLedgerSha256']:raise ValueError('Interrupted checkpoint or ledger changed before recovery')
        state=migrated_loader(checkpoint);settings=read(HERE.parent/'PLAN.json')['training']
        model,opt,rng=environment['restore'](state['trajectory'],settings)
        restored=environment['trajectory'](model,opt,rng,state['trajectory']['order'],state['trajectory']['cursor'],state['trajectory']['history'],2560)
        if not environment['exact'](restored,state['trajectory']):raise AssertionError('Durable2560 exact restore failed')
        del model,opt,rng,restored,state
    audit.update(amendmentSha256=a.amendment_sha,originalPlanSha256=a.plan_sha,originalSourceSha256=sha(sourcepath),
        model=a.model,stateMetadataMigration=state_metadata_audit,optimizerUpdatesByWrapperAudit=0,
        lossOrGenerationSelected=False,firstEpochDoseChanged=False)
    if a.audit_only:
        print(json.dumps(audit,indent=2));return
    if amendment.get('recoveryAuthorized') is not True:raise ValueError('Recovery not authorized')
    # The original trainer performs its own unchanged zero-update gradient and
    # state audit before any actual optimizer update.
    environment['main'](a)
    audit['stateMetadataMigration']=state_metadata_audit
    audit['preflightOnly']=a.preflight_only
    target=HERE/a.model/f'recovery-wrapper-audit-{time.time_ns()}.json'
    target.write_text(json.dumps(audit,indent=2)+'\n')
    if not a.preflight_only:
        receiptpath=HERE/a.model/'receipt.json';receipt=read(receiptpath)
        receipt['recoveryAmendmentSha256']=a.amendment_sha
        receipt['knownCompletedLostUpdates']=92 if a.model=='medium' else 0
        receipt['recoveryReplayUpdates']=92 if a.model=='medium' else 0
        receipt['lostStateBitwiseComparisonAvailable']=False if a.model=='medium' else None
        receipt['noOperationalClockCap']=True
        environment['write'](receiptpath,receipt)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--amendment',type=pathlib.Path,required=True);p.add_argument('--amendment-sha',required=True);p.add_argument('--plan',type=pathlib.Path,required=True);p.add_argument('--plan-sha',required=True);p.add_argument('--model',choices=['medium','small'],required=True);p.add_argument('--deadline',type=float,required=True);p.add_argument('--audit-only',action='store_true');p.add_argument('--preflight-only',action='store_true');main(p.parse_args())
