"""Stdlib-only postprocessing of frozen diagnostic outputs; never loads a model.

All positions are zero based. No context/quality labels are inferred from NLL.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import random

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONDITIONS = ('correct', 'mismatched', 'none')

def read(path):
    return json.loads(pathlib.Path(path).read_text())

def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def mean(values):
    values = list(values)
    return sum(values)/len(values) if values else None

def stats(rows):
    return {'tokens': len(rows), 'meanNll': mean(r['nll'] for r in rows),
            'top1Rate': mean(r['goldIsTop1'] for r in rows),
            'meanGoldRank': mean(r['goldRank'] for r in rows)}

def paired_summary(cases):
    return {'cases': len(cases), 'equalCaseMeanGain': mean(x['meanGain'] for x in cases),
            'tokenWeightedMeanGain': sum(x['sumGain'] for x in cases)/sum(x['tokens'] for x in cases) if cases else None,
            'positiveCases': sum(x['meanGain'] > 0 for x in cases),
            'zeroCases': sum(x['meanGain'] == 0 for x in cases),
            'negativeCases': sum(x['meanGain'] < 0 for x in cases)}

def grouped(items, key):
    groups = collections.defaultdict(list)
    for item in items:
        groups[key(item)].append(item)
    return groups

def macro_micro(cases):
    cases = [x for x in cases if x]
    summaries = [stats(x) for x in cases]
    return {'casesWithPositions': len(cases), 'tokenWeighted': stats([r for x in cases for r in x]),
            'equalCaseMacro': {k: mean(s[k] for s in summaries) for k in ('meanNll','top1Rate','meanGoldRank')}}

def distribution(values):
    observed = [x for x in values if x is not None]
    return {'cases':len(values), 'notObservedWithinAvailableHorizon':len(values)-len(observed),
            'observed':len(observed), 'meanObservedPosition':mean(observed),
            'countsByPosition':dict(sorted(collections.Counter(observed).items()))}

def bootstrap(cases, metadata):
    clusters = grouped(cases, lambda x: metadata[x['id']]['document'])
    docs = sorted(clusters)
    assert len(docs) == 403 and len(cases) == 1024
    rng = random.Random(2049)
    draws = []
    for _ in range(1000):
        sample = [x for doc in rng.choices(docs,k=len(docs)) for x in clusters[doc]]
        draws.append(mean(x['meanGain'] for x in sample))
    draws.sort()
    def quantile(p):
        index = p*(len(draws)-1); a = int(index); b = min(a+1,len(draws)-1)
        return draws[a]+(draws[b]-draws[a])*(index-a)
    return {'target':'Equal-pair macro mean mismatch-minus-correct NLL; resample whole target-document clusters',
            'documents':len(docs),'pairs':len(cases),'seed':2049,'replicates':1000,
            'pointEstimate':mean(x['meanGain'] for x in cases),'percentile95':[quantile(.025),quantile(.975)],
            'interpretation':'Descriptive resampling of supervised, anchor-selected TRAIN pool; no unseen-data inference'}

def historical(generations):
    base = ROOT/'training/language/round46/execution'
    paths = [base/'content-native-dev/new-python.json',base/'content-native-dev/new-rounding.json',
             base/'fixed-source-mrmp-dev/new-python.json',base/'fixed-source-mrmp-dev/new-unrounded.json']
    manifest_path = base/'artifact-manifest.json'
    manifest = read(manifest_path)
    reports = []
    for path in paths:
        data = read(path); old = {r['id']:r for r in data['rows']}
        entries = [r for r in manifest['files'] if r['path'].endswith(str(path.relative_to(base.parent)))]
        if len(entries) != 1 or entries[0]['sha256'] != sha(path):
            raise ValueError('Historical generation differs from frozen R46 manifest: '+str(path))
        comparisons=[]
        for row in generations:
            if row['condition'] != 'correct' or row['split'] != 'exposed-DEV' or row['id'] not in old: continue
            prior=old[row['id']]
            fields={'prefix':row['prefixText']==prior['prefix'],'text':row['text']==prior['text'],
                    'nonEosTokens':row['nonEosTokens']==prior['tokens'],'eos':row['eos']==prior['eos']}
            comparisons.append({'id':row['id'],'matches':fields,'allCoreFieldsMatch':all(fields.values()),
                'firstTokenDifference':next((i for i,(a,b) in enumerate(zip(row['nonEosTokens'],prior['tokens'])) if a!=b),
                    min(len(row['nonEosTokens']),len(prior['tokens'])) if len(row['nonEosTokens'])!=len(prior['tokens']) else None)})
        reports.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path),
            'kind':'raw selected checkpoint parity proof' if ('rounding' in path.name or 'unrounded' in path.name) else 'historical rounded-export Python generation',
            'proofSelectedStep':data.get('selectedStep'),'proofFullSequenceParity':data.get('completeRawVersusRoundedGenerationParity',data.get('completeRawVersusExportGenerationParity')),
            'compared':len(comparisons),'matching':sum(r['allCoreFieldsMatch'] for r in comparisons),'rows':comparisons})
    return {'manifestSha256':sha(manifest_path),'reports':reports,'policy':'Report all differences without repair; existing proofs do not establish new JS parity'}

def analyze(results):
    required=[results/name for name in ('tf-results.json','raw-generations.json','summary.json','receipt.json')]
    if not all(p.is_file() for p in required): raise ValueError('Require all four completed result files before analysis')
    receipt=read(required[3]); panel=read(HERE/'panel.json'); plan=read(HERE/'PLAN.json')
    if receipt['status']!='complete' or not all(receipt[k] for k in ('modelStateUnchanged','checkpointFilesUnchanged','globalTorchRngUnchanged','modelRemainsEval')):
        raise ValueError('Require complete integrity-verified inference receipt')
    if receipt['panelSha256']!=sha(HERE/'panel.json') or receipt['planSha256']!=sha(HERE/'PLAN.json'):
        raise ValueError('Frozen panel or PLAN differs from inference receipt')
    tf=read(required[0])['rows']; generations=read(required[1])['rows']; prior_summary=read(required[2])
    assert len(tf)==3147 and len(generations)==75
    metadata={x['id']:x for x in panel['cases']+panel['auxiliaryTfOnly']}
    bycase=grouped(tf,lambda r:r['id']); paired=[]; spans=[]
    for case_id, rows in bycase.items():
        cond={r['condition']:r for r in rows}; assert set(cond)==set(CONDITIONS)
        correct=cond['correct']; meta=metadata[case_id]
        for other in ('mismatched','none'):
            a=correct['tokens']; b=cond[other]['tokens']; assert len(a)==len(b)
            assert [r['goldToken'] for r in a]==[r['goldToken'] for r in b]==meta['goldTokens']
            delta=[y['nll']-x['nll'] for x,y in zip(a,b)]
            paired.append({'id':case_id,'caseGroup':correct['caseGroup'],'split':correct['split'],'source':correct['source'],
                'comparison':other+' minus correct NLL','tokens':len(delta),'sumGain':sum(delta),'meanGain':mean(delta),
                'genericGoldSurfaceTag':meta.get('genericGoldSurfaceTag','unannotated'),
                'unobservedSpeakerMention':meta.get('unobservedSpeakerMention','unannotated')})
        content={c:cond[c]['contentSpans'] for c in CONDITIONS}
        assert len({len(v) for v in content.values()})==1
        for j in range(len(content['correct'])):
            entry=content['correct'][j]; identity=(entry['startCharacter'],entry['endCharacter'],entry['text'])
            assert all((content[c][j]['startCharacter'],content[c][j]['endCharacter'],content[c][j]['text'])==identity for c in CONDITIONS)
            metrics={c:{'fullyTokenAligned':content[c][j]['fullyTokenAligned'],
                'wholeSpanTeacherTop1Exact':content[c][j]['wholeSpanTeacherTop1Exact'],
                'touched':stats(content[c][j]['touchedTokenScores']),
                'fullyContained':stats(content[c][j]['fullyContainedTokenScores'])} for c in CONDITIONS}
            gains={}
            for other in ('mismatched','none'):
                gains[other+' minus correct']={scope:(metrics[other][scope]['meanNll']-metrics['correct'][scope]['meanNll'])
                    if metrics['correct'][scope]['tokens'] else None for scope in ('touched','fullyContained')}
            spans.append({'id':case_id,'split':correct['split'],'source':correct['source'],'text':entry['text'],
                'startCharacter':identity[0],'endCharacter':identity[1],'touchedTokenPositions':entry['touchedTokenPositions'],
                'fullyContainedTokenPositions':entry['fullyContainedTokenPositions'],'conditions':metrics,'nllGains':gains})
    axes=lambda r:(r['caseGroup'],r['split'],r['source'])
    gains=[]
    for key,items in grouped(paired,lambda r:(*axes(r),r['comparison'])).items():
        gains.append({'group':key,**paired_summary(items)})
    stratified=[]
    for label in ('genericGoldSurfaceTag','unobservedSpeakerMention'):
        for key,items in grouped([r for r in paired if r['caseGroup']=='primary'],lambda r:(*axes(r),r['comparison'],json.dumps(r[label],ensure_ascii=False,sort_keys=True))).items():
            stratified.append({'annotation':label,'groupAndValue':key,**paired_summary(items)})
    bands={'firstToken':(0,1),'first8':(0,8),'positions8through31':(8,32),'positions32plus':(32,None)}
    positional=[]; history=[]
    for key,rows in grouped(tf,lambda r:(*axes(r),r['condition'])).items():
        for name,(start,end) in bands.items():
            positional.append({'group':key,'band':name,'startInclusive':start,'endExclusive':end,
                **macro_micro([r['tokens'][start:end] for r in rows])})
        if rows[0]['caseGroup']=='primary':
            for region in ('allMatchedAvailableIndices','before-departure','at-departure','after-departure'):
                own=[]; teacher=[]; differences=[]
                for row in rows:
                    probe=row['generatedHistoryProbe']; assert probe['K']==len(probe['rows'])
                    selected=[p for p in probe['rows'] if region=='allMatchedAvailableIndices' or p['region']==region]
                    own.append(selected); teacher.append([p['teacherForced'] for p in selected])
                    if selected: differences.append(mean(p['nllDifferenceFromTeacherForced'] for p in selected))
                history.append({'group':key,'region':region,'ownGeneratedHistoryGoldCounterfactual':macro_micro(own),
                    'teacherForcedSameIndices':macro_micro(teacher),'equalCaseMeanNllDifference':mean(differences),
                    'interpretation':'After departure these same-index gold probes are counterfactual sensitivity, never aligned accuracy or quality; EOS bounds preserved'})
    distributions=[]; numerical=[]
    for key,rows in grouped(generations,lambda r:(r['split'],r['source'],r['condition'])).items():
        distributions.append({'group':key,'firstGoldDeparturePosition':distribution([r['firstGoldDeparturePosition'] for r in rows]),
            'mechanicalRepetition':{str(n):distribution([(r['mechanicalRepeatedNgramOnsets'][str(n)] or {}).get('repeatCompletionPosition') for r in rows]) for n in (3,4)},
            'eosCases':sum(r['eos'] for r in rows),'generatedNonEosLengths':distribution([r['generatedNonEosTokens'] for r in rows]),
            'interpretation':'Token departure and exact ngram recurrence are mechanical events, not harmful quality onset; null may mean horizon ended'})
        refs=[r['numericalReference'] for r in rows]
        numerical.append({'group':key,'comparedPositions':sum(r['comparedPositions'] for r in refs),
            'argmaxDisagreements':sum(r['argmaxDisagreements'] for r in refs),'toleranceExceedances':sum(r['toleranceExceedances'] for r in refs),
            'maxAbsoluteLogitError':max((r['maxAbsoluteLogitError'] for r in refs if r['maxAbsoluteLogitError'] is not None),default=None),
            'tolerance':plan['numericalReferenceTolerance'],'scope':'Identical preceding history, includes departure prediction; raw Python only'})
    auxiliary=[r for r in paired if r['caseGroup']=='auxiliary-supervisedTRAIN' and r['comparison']=='mismatched minus correct NLL']
    historical_reference=plan['historicalPoolReference']; reference_path=ROOT/historical_reference['path']
    if sha(reference_path)!=historical_reference['sha256']:raise ValueError('Historical pool reference hash differs from PLAN')
    historical_data=read(reference_path); historical_mean=historical_data['groups']['auxiliary1024']['meanContextGain']
    assert historical_mean==historical_reference['meanContextGain']
    historical_rows = {(r['document'],r['turn']):r for r in historical_data['groups']['auxiliary1024']['rows']}
    matched = []
    for row in auxiliary:
        meta = metadata[row['id']]
        old = historical_rows[(meta['document'],meta['targetOrdinal'])]
        matched.append({'id':row['id'],'historicalGain':old['contextGain'],
            'currentGain':row['meanGain'],'difference':row['meanGain']-old['contextGain']})
    assert len(matched)==1024
    current_mean=mean(r['meanGain'] for r in auxiliary)
    return {'scope':'Postprocessing only; no model, optimizer, output repair, checkpoint selection or public change',
        'sourceSha256':sha(__file__),'inputHashes':{p.name:sha(p) for p in required},'panelSha256':sha(HERE/'panel.json'),'planSha256':sha(HERE/'PLAN.json'),
        'perCaseContextEffects':paired,'contextEffectGroups':gains,'manualAnnotationStrata':stratified,
        'positionBandMetrics':positional,'pairedContentSpans':spans,
        'contentPolicy':'Same frozen manually labelled word/inflected span across conditions; touched tokens may cross word boundaries. Whole-span teacher top1 only when both endpoints token aligned; no free-generation word accuracy claim.',
        'generatedHistoryMatchedIndices':history,'generationDistributions':distributions,'numericalReferenceGroups':numerical,
        'auxiliaryDocumentClusterBootstrap':bootstrap(auxiliary,metadata),
        'historicalAuxiliaryPoolCheck':{'referencePath':historical_reference['path'],'referenceSha256':sha(reference_path),
            'historicalMeanGain':historical_mean,'currentMeanGain':current_mean,'difference':current_mean-historical_mean,'matchedPairs':len(matched),
            'maximumAbsolutePairGainDifference':max(abs(r['difference']) for r in matched),'perPairComparison':matched,
            'policy':'Exact same supervised pool targets/mismatches; raw FP32 numerical consistency check, no threshold or force fitting'},
        'historicalDevGenerationComparison':historical(generations),
        'inferenceSummaryNumericalCounts':{k:v for k,v in prior_summary.items() if k.startswith('primaryNumerical')},
        'limitations':['BOS-only changes target absolute positions; correct versus equal-length mismatched is the controlled contrast.',
            'Mismatched contexts can admit valid generic replies; gold is authentic but not uniquely correct.',
            'TRAIN supervised pool is anchor-selected; all DEV cases already exposed; descriptive only.',
            'Generic/unobserved-mention tags describe gold surfaces, never model quality or speaker truth. Unannotated cases stay separate.',
            'No generated-history position after departure is aligned gold language accuracy. Manual full-output quality review remains separate.']}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--results',type=pathlib.Path,default=HERE/'results')
    args=parser.parse_args();output=args.results/'analysis.json'
    if output.exists():raise ValueError('Refuse overwrite of existing analysis.json')
    result=analyze(args.results)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'output':str(output),'contextEffectGroups':result['contextEffectGroups'],
        'historicalAuxiliaryPoolCheck':result['historicalAuxiliaryPoolCheck'],
        'auxiliaryDocumentClusterBootstrap':result['auxiliaryDocumentClusterBootstrap']},ensure_ascii=False))

if __name__=='__main__':main()
