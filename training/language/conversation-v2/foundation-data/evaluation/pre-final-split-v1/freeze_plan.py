"""Freeze zero-update benchmark inputs only after final combined family split."""
import argparse,json,pathlib
from benchmark_core import HERE,BASE,REPO,read,sha,prepare_cases,check_final_split

def main(a):
    human=read(HERE/'human-dev.json');synthetic=read(HERE/'researcher-input-dev.json')
    if human['articleSplitSha256']!=sha(a.final_split):raise ValueError('Rebuild against final split before freeze')
    split_audit=check_final_split(human,read(a.final_split))
    prepared=prepare_cases(human,synthetic,read(BASE/'data/tokenizer.json'))
    names=['benchmark_core.py','run_benchmark.py','build_dev.py','build_challenges.py','freeze_plan.py',
        'human-dev.json','human-dev-audit.json','selection-history.json','source-quality-issues.json',
        'quarantined-source-cases.json','researcher-input-dev.json','RUBRIC.json']
    inputs=[HERE/n for n in names]+[BASE/'data/tokenizer.json',BASE/'new_tokenizer.py',BASE/'core.py',
        BASE/'eval_core.py',BASE/'epoch1/eval_chunk_loader.py',BASE/'PLAN.json',REPO/'training/language/model.py']
    plan=dict(status='FROZEN_CANDIDATE_DEV_PREPARATION_ONLY',inferenceAuthorized=False,optimizerUpdatesPermitted=0,
        sourceLicenseAdmission='Candidate source not admitted for training; no source-quality/legal issue hidden by evaluation',
        finalCombinedSplitSha256=sha(a.final_split),splitAudit=split_audit,
        codeAndDataReceipts={str(p.relative_to(REPO)):sha(p)for p in inputs},
        checkpointSha256='5ad249d2c8d5910090c9baba94f94483e9c037139d15b9c4360fd3e975409544',
        modelConfig=read(BASE/'PLAN.json')['models']['medium'],checkpointPolicy='Fixed medium terminal3470 only; no score-based selection',
        cases=len(prepared),caseIds=[r['id']for r in prepared],
        supportedCases=sum(r['generationSupported']for r in prepared),
        unsupportedCaseIds=[r['id']for r in prepared if not r['generationSupported']],
        generation='Full-vocabulary greedy, genuineEOS2, max64 QA/researcher or128prose; no crop/mask/penalty/repair',
        promptContract='HumanA/B diagnostic IDs3/4 with evaluator wrapper. Current model has no demonstrated learned AI-response role; failures are not a clean causal proof of capacity or context inability.',
        modelInferenceExecuted=False,sealedTestCreated=False,sealedTestUsed=False,formalAdoption=False,
        noGeneratedTrainingPositives=True,independentNativeHumanEvaluationCompleted=False)
    (HERE/'PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    (HERE/'final-split-audit.json').write_text(json.dumps(split_audit,indent=2)+'\n')
    print(json.dumps(dict(planSha256=sha(HERE/'PLAN.json'),cases=len(prepared),supported=plan['supportedCases'],inferenceAuthorized=False)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--final-split',type=pathlib.Path,required=True);main(p.parse_args())
