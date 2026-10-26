"""Append-only, non-numerical repair of a preregistered resume audit pathname."""
import argparse,ast,copy,hashlib,json,pathlib,sys,time
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[3]
OLD="pfpath=out/('preflight-v2.json' if a.preflight_only else 'run-zero-update-preflight.json')"
NEW="pfpath=out/(f'resume-zero-update-{unique}-{actual}-{time.time_ns()}.json' if a.resume else ('preflight-v2.json' if a.preflight_only else 'run-zero-update-preflight.json'))"
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text())
def transform(source):
    if source.count(OLD)!=1:raise ValueError('Exactly one preregistered pathname assignment required')
    changed=source.replace(OLD,NEW);oldtree=ast.parse(source);newtree=ast.parse(changed)
    old=[x for x in ast.walk(oldtree)if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name)and x.targets[0].id=='pfpath']
    new=[x for x in ast.walk(newtree)if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name)and x.targets[0].id=='pfpath']
    if len(old)!=1 or len(new)!=1:raise ValueError('Unexpected audit pathname AST')
    normalized=copy.deepcopy(newtree)
    node=[x for x in ast.walk(normalized)if isinstance(x,ast.Assign)and len(x.targets)==1 and isinstance(x.targets[0],ast.Name)and x.targets[0].id=='pfpath'][0]
    node.value=copy.deepcopy(old[0].value)
    if ast.dump(oldtree)!=ast.dump(normalized):raise AssertionError('Transformation changed additional Python semantics')
    return changed,dict(originalLine=OLD,replacementLine=NEW,onlyPfpathAssignmentChanged=True,allOtherAstNodesIdentical=True,effectiveSourceSha256=hashlib.sha256(changed.encode()).hexdigest())
def main(a):
    if sha(a.amendment)!=a.amendment_sha:raise ValueError('Amendment SHA mismatch')
    amendment=read(a.amendment)
    for p,h in amendment['codeAndInputReceipts'].items():
        if sha(REPO/p)!=h:raise ValueError('Frozen amendment input changed: '+p)
    if sha(a.plan)!=amendment['originalPlanSha256'] or a.plan_sha!=amendment['originalPlanSha256']:raise ValueError('Wrong original plan')
    if a.model!='medium' or a.deadline!=amendment['deadlineUnix']:raise ValueError('Wrong fixed resume model/deadline')
    manifest=pathlib.Path(amendment['stoppedCheckpointManifest']);ledger=HERE/a.model/'optimizer-ledger.jsonl'
    if read(manifest)['sha256']!=amendment['stoppedCheckpointSha256'] or sha(ledger)!=amendment['stoppedLedgerSha256']:raise ValueError('Stopped state/ledger changed')
    sourcepath=HERE/'continue_train.py';changed,audit=transform(sourcepath.read_text())
    if audit['effectiveSourceSha256']!=amendment['effectiveSourceSha256']:raise ValueError('Effective source mismatch')
    audit.update(amendmentSha256=a.amendment_sha,originalSourceSha256=sha(sourcepath),originalPlanSha256=a.plan_sha,optimizerUpdatesByWrapper=0)
    if a.audit_only:
        print(json.dumps(audit,indent=2));return
    if amendment.get('resumeAuthorized') is not True:raise ValueError('Resume not authorized')
    environment={'__file__':str(sourcepath),'__name__':'_epoch1_append_only_resume_audit_fix'}
    exec(compile(changed,str(sourcepath), 'exec'),environment)
    # The original main validates its original plan, source, all data receipts,
    # exact restored state and ledger. Only the audit receipt pathname differs.
    a.resume=True;a.preflight_only=False
    environment['main'](a)
    auditpath=HERE/a.model/'resume-wrapper-audit.json'
    if auditpath.exists():raise ValueError('Refuse wrapper audit overwrite')
    auditpath.write_text(json.dumps(audit,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--amendment',type=pathlib.Path,required=True);p.add_argument('--amendment-sha',required=True);p.add_argument('--plan',type=pathlib.Path,required=True);p.add_argument('--plan-sha',required=True);p.add_argument('--model',choices=['medium'],required=True);p.add_argument('--deadline',type=float,required=True);p.add_argument('--audit-only',action='store_true');main(p.parse_args())
