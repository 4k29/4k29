"""Frozen own-checkpoint context-use diagnostic; inference only, no optimizers.

Run only after external panel/plan/code freeze. Outputs exposed TRAIN/DEV
diagnostics, never a new TEST or model-selection result.
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import platform
import sys
import time

import torch

from diagnostic_core import (aggregate, byte_payload, content_spans, fence,
    generated_history_probe, greedy, macro_and_token_weighted,
    repeated_ngram_onset, teacher_forced)

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]


def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(pathlib.Path(path).read_text())


def write(path, value):
    pathlib.Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def state_digest(state):
    h = hashlib.sha256()
    for name, value in sorted(state.items()):
        t = value.detach().cpu().contiguous()
        h.update(name.encode()); h.update(str((str(t.dtype),tuple(t.shape))).encode())
        h.update(t.numpy().tobytes())
    return h.hexdigest()


def repo_path(name):
    path = (REPO / name).resolve()
    if not path.is_relative_to(REPO) or not path.is_file():
        raise ValueError('Input must be an existing repository file: '+name)
    return path


def load_model(panel):
    raw_path = repo_path(panel['checkpointPath'])
    aligned_path = repo_path(panel['alignedCheckpointPath'])
    if sha(raw_path) != panel['expectedCheckpointSha256'] or sha(aligned_path) != panel['alignedSha256']:
        raise ValueError('Frozen raw/aligned checkpoint SHA mismatch; no restoration permitted')
    raw = torch.load(raw_path, map_location='cpu', weights_only=False)
    aligned = torch.load(aligned_path, map_location='cpu', weights_only=False)
    if raw['selectedStep'] != 9500 or aligned['step'] != 9500 or raw['config'] != aligned['config']:
        raise ValueError('Expected exact own R46 selected step9500')
    weights = raw['state']
    for reference in [aligned['model'], aligned['beststate']]:
        if weights.keys() != reference.keys() or any(not torch.equal(weights[k], reference[k]) for k in weights):
            raise ValueError('Raw selected weights differ from full aligned selected state')
    if any(v.dtype != torch.float32 or not bool(torch.isfinite(v).all()) for v in weights.values()):
        raise ValueError('Expected finite raw FP32 parameters')
    model_path = REPO / 'training/language/model.py'
    spec = importlib.util.spec_from_file_location('_own_context_diagnostic_decoder', model_path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    # Constructor initialization uses RNG; restore caller state before inference.
    rng = torch.get_rng_state().clone()
    try:
        model = module.Decoder(raw['config'])
        model.load_state_dict(weights, strict=True)
        model.eval()
    finally:
        torch.set_rng_state(rng)
    if not torch.equal(rng, torch.get_rng_state()):
        raise AssertionError('Model construction failed to restore RNG')
    return model, {'rawCheckpointBeforeSha256': sha(raw_path),
        'alignedCheckpointBeforeSha256': sha(aligned_path), 'selectedStep': raw['selectedStep'],
        'rawMatchesAlignedModelAndBestState': True, 'modelSourceSha256': sha(model_path)}, raw_path, aligned_path


def validate_cases(panel, pieces, context):
    primary = panel['cases']; auxiliary = panel['auxiliaryTfOnly']
    if len(primary) != 25 or len(auxiliary) != 1024:
        raise ValueError('Frozen panel must contain25 primary and1024 auxiliary TF-only cases')
    ids = [case['id'] for case in primary+auxiliary]
    if len(set(ids)) != len(ids): raise ValueError('Duplicate diagnostic case ID')
    for case in primary+auxiliary:
        gold = case['goldTokens']
        if not gold or any(type(t) is not int or not 6 <= t < len(pieces) for t in gold):
            raise ValueError('Gold must contain original non-special IDs and no BOS/EOS')
        if b''.join(pieces[t] for t in gold) != case['targetText'].encode('utf8'):
            raise ValueError('Gold bytes do not match exact targetText')
        if set(case['conditions']) != {'correct','mismatched','none'}:
            raise ValueError('Exactly three frozen conditions required')
        if len(case['conditions']['correct']['prefixTokens']) != len(case['conditions']['mismatched']['prefixTokens']):
            raise ValueError('Correct and mismatched contexts must have exactly equal token lengths')
        for condition, data in case['conditions'].items():
            prefix = data['prefixTokens']
            if not prefix or prefix[0] != 1 or any(type(t) is not int or not 0 <= t < len(pieces) for t in prefix):
                raise ValueError('Condition must contain exact BOS-containing prefix IDs')
            if prefix.count(1) != 1 or 2 in prefix:
                raise ValueError('Do not insert duplicate BOS or EOS into a diagnostic prefix')
            if condition == 'none' and prefix != [1]: raise ValueError('No-context condition is exactly BOS')
            if b''.join(pieces[t] for t in prefix[1:]) != data['prefixText'].encode('utf8'):
                raise ValueError('Prefix token bytes and full prefixText differ')
            if len(prefix)+len(gold) > context: raise ValueError('TF exceeds original context')
            if case in primary and (len(prefix) > 64 or len(prefix)+192 > context):
                raise ValueError('Primary full192 generation must fit without truncation')
        # Validate manual pre-output labels before the first inference call.
        dummy = [{'goldIsTop1':False,'nll':0.,'goldRank':1,'goldProbability':0.,
                  'goldMinusBestOtherLogit':0.} for _ in gold]
        content_spans(case['targetText'], gold, pieces, case['contentSpans'], dummy)


def summarize(tf_rows):
    groups = {}
    for row in tf_rows:
        key = (row['caseGroup'], row['split'], row['source'], row['condition'])
        groups.setdefault(key, []).append(row)
    reports = []
    for (case_group, split, source, condition), rows in groups.items():
        item = {'caseGroup':case_group, 'split':split,'source':source,'condition':condition,
                'teacherForcedGold':macro_and_token_weighted([r['tokens'] for r in rows]),
                'meanEosProbabilityAtGoldEnd':sum(r['eosAtGoldEnd']['probability'] for r in rows)/len(rows)}
        if case_group == 'primary':
            item['generatedHistoryGoldCounterfactual'] = macro_and_token_weighted([r['generatedHistoryProbe']['rows'] for r in rows])
            item['sameIndicesTeacherForced'] = macro_and_token_weighted([r['tokens'][:r['generatedHistoryProbe']['K']] for r in rows])
            item['byDepartureRegion'] = {region: macro_and_token_weighted([
                [t for t in r['generatedHistoryProbe']['rows'] if t['region'] == region] for r in rows])
                for region in ['before-departure','at-departure','after-departure']}
        reports.append(item)
    # Equal-case and token-weighted context effects use identical full gold IDs.
    cases = {}
    for row in tf_rows:
        cases.setdefault((row['caseGroup'], row['split'], row['source'], row['id']), {})[row['condition']] = row
    effects = {}
    for (group, split, source, case_id), conditions in cases.items():
        key = (group,split,source)
        for other in ['mismatched','none']:
            correct = conditions['correct']['tokens']; wrong = conditions[other]['tokens']
            delta = [w['nll']-c['nll'] for c,w in zip(correct,wrong,strict=True)]
            effects.setdefault((*key,other), []).append(delta)
    context_effects = []
    for (group,split,source,other), cases_delta in effects.items():
        context_effects.append({'caseGroup':group,'split':split,'source':source,'comparison':other+' minus correct NLL',
            'cases':len(cases_delta),'equalCaseMeanGain':sum(sum(v)/len(v) for v in cases_delta)/len(cases_delta),
            'tokenWeightedMeanGain':sum(sum(v) for v in cases_delta)/sum(len(v) for v in cases_delta)})
    return {'groups':reports,'contextEffects':context_effects,
            'poolingPolicy':'TRAIN and exposed DEV, sources, primary and auxiliary-supervised TRAIN are reported separately; macro and token-weighted metrics distinct',
            'generatedHistoryInterpretation':'Same-gold counterfactual sensitivity after departure, not aligned accuracy or proof of semantic context use'}


def markdown(rows):
    out = ['# Fixed-checkpoint raw generations', '',
           'Python raw FP32 only. Full prefixes and all continuations shown without repair. Mechanical repetition is not semantic quality onset.', '']
    for row in rows:
        out += ['## '+row['id']+' / '+row['condition'], '',
                'Split: '+row['split']+'; source: '+row['source'], '', 'Full prefix:', '',
                fence(row['prefixText']), '', 'Continuation:', '']
        if row['strictUtf8']:
            out += [fence(row['text'])]
        else:
            out += ['Invalid strict UTF8; text is null. Original continuation bytes:', '', fence(row['rawBytesHex'])]
        out += ['', 'EOS: '+str(row['eos'])+'; generated non-EOS IDs: '+str(row['generatedNonEosTokens']), '',
                'Token IDs including EOS when emitted:', '', fence(json.dumps(row['tokensIncludingEos'])), '']
    return '\n'.join(out)+'\n'


def run(args):
    if sha(args.panel) != args.panel_sha256 or sha(args.plan) != args.plan_sha256:
        raise ValueError('Explicit frozen panel/plan SHA mismatch')
    panel = read(args.panel)
    plan = read(args.plan)
    if 'codeHashes' in plan:
        expected_names = {'run_diagnostic.py','diagnostic_core.py','test_diagnostic.py'}
        if set(plan['codeHashes']) != expected_names:
            raise ValueError('Plan codeHashes must bind all three diagnostic source files')
        for name, expected in plan['codeHashes'].items():
            if sha(HERE/name) != expected:
                raise ValueError('Frozen diagnostic code SHA mismatch: '+name)
    for key, expected in [('primaryCaseCount',25),('auxiliaryCaseCount',1024),('maxNewTokens',192),('threads',1)]:
        if key in plan and plan[key] != expected:
            raise ValueError('Plan setting differs from fixed diagnostic: '+key)
    output = args.output.resolve()
    if not output.is_relative_to(HERE) or output.exists():
        raise ValueError('Output must be a NEW directory inside this diagnostic folder')
    tokenizer_path = repo_path(panel['tokenizerPath'])
    if sha(tokenizer_path) != panel['tokenizerSha256']: raise ValueError('Frozen tokenizer SHA mismatch')
    tokenizer = read(tokenizer_path); pieces = [bytes.fromhex(s) for s in tokenizer['bytes']]
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True); torch.set_default_dtype(torch.float32)
    rng = torch.get_rng_state().clone()
    model, provenance, raw_path, aligned_path = load_model(panel)
    assert torch.equal(rng,torch.get_rng_state())
    validate_cases(panel,pieces,model.config['context'])
    initial_state = state_digest(model.state_dict())
    output.mkdir()
    started = time.monotonic()
    receipt = {'panelSha256':args.panel_sha256,'planSha256':args.plan_sha256,
        'tokenizerSha256':panel['tokenizerSha256'],
        'codeSha256':{name:sha(HERE/name) for name in ['run_diagnostic.py','diagnostic_core.py','test_diagnostic.py']},
        'environment':{'python':sys.version,'torch':torch.__version__,'platform':platform.platform(),
                       'threads':torch.get_num_threads(),'precision':'FP32','device':'cpu','deterministicAlgorithms':True},
        **provenance, 'initialModelStateDigest':initial_state,
        'globalTorchRngBeforeInferenceSha256':hashlib.sha256(rng.numpy().tobytes()).hexdigest(),
        'actualOptimizerObjectsConstructed':0,'actualOptimizerUpdates':0,'newTestAccess':False,
        'scope':'Frozen own R46 selected raw model; Python-only diagnostic; no JS/export parity claim',
        'primaryCases':25,'primaryGenerationsExpected':75,'auxiliaryTfOnlyCases':1024,
        'auxiliaryTfOnlyProvenance':panel.get('auxiliaryTfOnlyProvenance'),
        'referencePoolUniqueDocuments':panel.get('referencePoolUniqueDocuments'), 'status':'running'}
    write(output/'receipt.json',receipt)
    tf_rows=[]; generations=[]; references=[]; seen_reference_groups=set()
    try:
        for group,cases in [('primary',panel['cases']),('auxiliary-supervisedTRAIN',panel['auxiliaryTfOnly'])]:
            for case in cases:
                for condition,data in case['conditions'].items():
                    prefix=data['prefixTokens'];gold=case['goldTokens']
                    logits, tf=teacher_forced(model,prefix,gold)
                    base={'id':case['id'],'caseGroup':group,'split':case['split'],'source':case['source'],
                          'condition':condition,'targetText':case['targetText'],'goldTokens':gold,
                          'prefixText':data['prefixText'],'prefixTokens':prefix,'inputTokensWithBos':len(prefix)}
                    row={**base,**tf,'teacherForcedSummary':aggregate(tf['tokens']),
                         'contentSpans':content_spans(case['targetText'],gold,pieces,case['contentSpans'],tf['tokens'])}
                    if group=='primary':
                        generation=greedy(model,prefix,gold,logits,pieces,max_new=192)
                        generation['mechanicalRepeatedNgramOnsets']={str(n):repeated_ngram_onset(generation['nonEosTokens'],n) for n in [3,4]}
                        generation['manualQualityDegradationOnset']=None
                        generation['manualQualityStatus']='Pending independent complete-output review; mechanical repeat is not semantic onset'
                        generations.append({**base,**generation})
                        row['generatedHistoryProbe']=generated_history_probe(model,prefix,gold,generation,tf['tokens'])
                        key=(case['split'],case['source'])
                        if condition=='correct' and key not in seen_reference_groups:
                            references.append({'id':case['id'],'condition':condition,'prefixTokens':prefix,
                                'firstPositionLogits':logits[0].tolist(),
                                'selection':'First primary correct-context case in frozen panel order per split/source; no outcome selection'})
                            seen_reference_groups.add(key)
                    tf_rows.append(row)
                print(group,case['id'],'complete',flush=True)
        if len(generations)!=75 or len(tf_rows)!=(25+1024)*3:
            raise AssertionError('Diagnostic case accounting mismatch')
        write(output/'raw-generations.json',{'scope':receipt['scope'],'rows':generations})
        write(output/'tf-results.json',{'goldDoesNotIncludeEos':True,'rows':tf_rows})
        write(output/'sampled-reference-logits.json',{'scope':'Raw Python selected checkpoint only; not JS or export parity','rows':references})
        summary=summarize(tf_rows)
        summary.update(primaryGenerations=75,auxiliaryTfOnlyCases=1024,
            primaryNumericalReferenceArgmaxDisagreements=sum(g['numericalReference']['argmaxDisagreements'] for g in generations),
            primaryNumericalReferenceToleranceExceedances=sum(g['numericalReference']['toleranceExceedances'] for g in generations),
            manualReviewComplete=False,languageImprovementClaim=False)
        write(output/'summary.json',summary)
        (output/'ALL_GENERATIONS.md').write_text(markdown(generations))
        receipt['status']='complete'
    except Exception as error:
        receipt['status']='failed';receipt['failure']={'type':type(error).__name__,'message':str(error)}
        # Keep completed rows; do not relabel partial coverage as a complete run.
        write(output/'partial-tf-results.json',{'rows':tf_rows})
        write(output/'partial-generations.json',{'rows':generations})
        raise
    finally:
        receipt.update(completedTfRows=len(tf_rows),completedPrimaryGenerations=len(generations),
            finalModelStateDigest=state_digest(model.state_dict()),
            rawCheckpointAfterSha256=sha(raw_path),alignedCheckpointAfterSha256=sha(aligned_path),
            globalTorchRngAfterInferenceSha256=hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest(),
            modelRemainsEval=not model.training,elapsedSeconds=time.monotonic()-started)
        receipt['modelStateUnchanged']=receipt['finalModelStateDigest']==initial_state
        receipt['checkpointFilesUnchanged']=(receipt['rawCheckpointAfterSha256']==provenance['rawCheckpointBeforeSha256'] and receipt['alignedCheckpointAfterSha256']==provenance['alignedCheckpointBeforeSha256'])
        receipt['globalTorchRngUnchanged']=torch.equal(rng,torch.get_rng_state())
        if not all(receipt[k] for k in ['modelStateUnchanged','checkpointFilesUnchanged','globalTorchRngUnchanged','modelRemainsEval']):
            receipt['status']='failed';receipt['integrityFailure']=True
        write(output/'receipt.json',receipt)
    if receipt['status']!='complete':raise AssertionError('Inference integrity failure; inspect receipt')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel',type=pathlib.Path,required=True)
    parser.add_argument('--panel-sha256',required=True)
    parser.add_argument('--plan',type=pathlib.Path,required=True)
    parser.add_argument('--plan-sha256',required=True)
    parser.add_argument('--output',type=pathlib.Path,required=True)
    run(parser.parse_args())
