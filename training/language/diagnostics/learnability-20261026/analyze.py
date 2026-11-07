"""Descriptive frozen-panel summaries; exchange-pair cluster bootstrap."""
import json, pathlib, random, hashlib
H=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def mean(xs):return sum(xs)/len(xs)
def interval(values):
    rng=random.Random(2049); estimates=sorted(mean([values[rng.randrange(len(values))] for _ in values]) for _ in range(2000))
    return [estimates[49],estimates[1949]]
def main():
    p=read(H/'candidate-panel.json'); cs={c['id']:c for c in p['cases']}
    endpoints={e:read(H/'results'/e/'tf.json') for e in ['baseline','A','B']}
    lookup={(e,r['id'],r['condition']):r for e,rs in endpoints.items()for r in rs}
    relation={r['id']:r['permutedTargetRelation']for r in read(H/'independent-data-review.json')['rows']}
    second={r['id']:r for r in read(H/'independent-evaluation-preflight.json')['rows']}
    groups={g:[c['id'] for c in p['cases']if c['group']==g]for g in ['fit','heldaside']}
    for g in ['fit','heldaside']:
        base=groups[g]
        groups[g+'/both-reviewers-clear']=[i for i in base if relation[i]=='clear_mismatch' and second[i]['BRelation']=='clear_mismatch']
        groups[g+'/other-or-disputed']=[i for i in base if i not in groups[g+'/both-reviewers-clear']]
        groups[g+'/target-at-most24tokens']=[i for i in base if len(cs[i]['goldTokens'])<=24]
        groups[g+'/target-over24tokens']=[i for i in base if len(cs[i]['goldTokens'])>24]
    result={'scope':'Descriptive TRAIN assay; heldaside not updated by this assay but previously supervised by R46; not unseen TEST',
        'bootstrap':'2000 exchange-pair cluster replicates, seed2049, percentile2.5/97.5; panel-conditional, not population generalization', 'groups':[],'caseMetrics':[]}
    for g,ids in groups.items():
        for e in endpoints:
            for condition in ['correct','mismatched']:
                rs=[lookup[e,i,condition]for i in ids]; toks=[t for r in rs for t in r['tokens']]
                result['groups'].append({'group':g,'endpoint':e,'condition':condition,'cases':len(rs),'tokens':len(toks),
                    'macroNll':mean([r['aggregate']['meanNll']for r in rs]),'tokenWeightedNll':mean([r['nll']for r in toks]),
                    'top1Rate':mean([r['goldIsTop1']for r in toks]),'eosAtGoldEndProbability':mean([r['eosAtGoldEnd']['probability']for r in rs])})
        deltas={};case=[]
        for i in ids:
            n={(e,c):lookup[e,i,c]['aggregate']['meanNll']for e in endpoints for c in ['correct','mismatched']}
            gains={e:n[e,'mismatched']-n[e,'correct']for e in endpoints}
            delta=gains['A']-gains['B'];deltas[i]=delta
            case.append({'id':i,'group':g,'goldTokens':len(cs[i]['goldTokens']),'review1BRelation':relation[i],
                'review2':second[i], 'nll':{e:{c:n[e,c]for c in ['correct','mismatched']}for e in endpoints},
                'contextGain':gains,'contextGainAminusB':delta,
                'ownFitDropA':n['baseline','correct']-n['A','correct'],
                'ownFitDropB':n['baseline','mismatched']-n['B','mismatched']})
        pairvalues=[mean([deltas[i]for i in pair['rowIds']])for pair in p['permutationPairs']if pair['group']==g]
        result.setdefault('pairedEffects',[]).append({'group':g,'contextGainAminusB':mean(list(deltas.values())),
            'clusterBootstrap95':interval(pairvalues) if pairvalues else None,'exchangePairs':len(pairvalues),
            'positiveCases':sum(d>0 for d in deltas.values()),
            'ownFitImprovedA':sum(x['ownFitDropA']>0 for x in case),'ownFitImprovedB':sum(x['ownFitDropB']>0 for x in case)})
        if '/' not in g: result['caseMetrics'].extend(case)
    write(H/'results/analysis.json',result)
    print(json.dumps({k:v for k,v in result.items()if k!='caseMetrics'},ensure_ascii=False,indent=2))
    allgen=[]
    for e in endpoints:allgen.extend(read(H/'results'/e/'generations.json'))
    from sys import path
    path.insert(0,str(H.parent/'context-use-20261025'))
    from diagnostic_core import fence
    text=['# All raw continuations','', 'Full unmodified bytes/text and token IDs. No outputs repaired.']
    blind=[];key=[]
    for r in allgen:
        token=hashlib.sha256(('blind-assay-v1|'+r['endpoint']+'|'+r['id']+'|'+r['condition']).encode()).hexdigest()[:16]
        blind.append({'blindId':token,'group':r['group'],'prefixText':r['prefixText'],'text':r['text'],'strictUtf8':r['strictUtf8']})
        key.append({'blindId':token,'endpoint':r['endpoint'],'id':r['id'],'condition':r['condition']})
        text.extend(['','## '+r['endpoint']+' / '+r['id']+' / '+r['condition'],'', 'Prefix:',fence(r['prefixText']),'Continuation:',fence(r['text'] if r['strictUtf8']else r['rawBytesHex']),'Token IDs incl emitted EOS:',fence(json.dumps(r['tokensIncludingEos']))])
    blind.sort(key=lambda r:r['blindId']);write(H/'results/blind-input.json',blind);write(H/'results/blind-key.json',key)
    (H/'results/ALL_GENERATIONS.md').write_text('\n'.join(text)+'\n')
if __name__=='__main__':main()
