"""Post-output arithmetic only. No model, updates, selection or new gate."""
import hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
    p=read(H/'candidate-panel.json');cs={c['id']:c for c in p['cases']}
    allgen=[g for e in ['baseline','A','B']for g in read(H/'results'/e/'generations.json')]
    result={'scope':'Exact canonical prefix is memorization, not whole-meaning success','groups':[]}
    for e in ['baseline','A','B']:
        for group in ['fit','heldaside']:
            for cond in ['correct','mismatched']:
                rows=[g for g in allgen if g['endpoint']==e and g['group']==group and g['condition']==cond]
                matches=[g for g in rows if g['nonEosTokens'][:len(cs[g['id']]['goldTokens'])]==cs[g['id']]['goldTokens']]
                result['groups'].append({'endpoint':e,'group':group,'condition':cond,'n':len(rows),
                    'goldPrefixExact':len(matches),'goldAndImmediateEos':sum(g['tokensIncludingEos']==cs[g['id']]['goldTokens']+[2]for g in rows),
                    'goldPrefixThenAdditionalTokens':sum(len(g['nonEosTokens'])>len(cs[g['id']]['goldTokens'])for g in matches),
                    'eos':sum(g['eos']for g in rows),'repeated4gram':sum(g['repeated4gram']is not None for g in rows),
                    'meanLength':sum(g['generatedNonEosTokens']for g in rows)/len(rows),
                    'invalidUtf8':sum(not g['strictUtf8']for g in rows),'nonEosSpecial':sum(g['nonEosContainsSpecialTokens']for g in rows)})
    result['numerics']={'teacherSequentialMaxError':max(g['numericalReference']['maxAbsoluteLogitError'] or 0 for g in allgen),
        'argmaxDisagreements':sum(g['numericalReference']['argmaxDisagreements']for g in allgen),
        'toleranceExceedances':sum(g['numericalReference']['toleranceExceedances']for g in allgen)}
    write(H/'results/generation-mechanics.json',result)
    paths=[H/'results/fit-blind-reading.json',H/'results/heldaside-blind-reading.json']
    if not all(p.is_file()for p in paths):return
    readings=[r for p in paths for r in read(p)['rows']]
    keys={r['blindId']:r for r in read(H/'results/blind-key.json')}
    assert len(readings)==192 and len({r['blindId']for r in readings})==192
    flags=['naturalWhole','meaningfulWhole','appropriateWhole','specificContentAppropriate','genericOnly','harmfulRepetition','topicDrift']
    merged=[{**r,**keys[r['blindId']]}for r in readings];stats=[]
    for group in ['fit','heldaside']:
        for e in ['baseline','A','B']:
            for cond in ['correct','mismatched']:
                rows=[r for r in merged if r['endpoint']==e and r['condition']==cond and cs[r['id']]['group']==group]
                assert len(rows)==16
                stats.append({'group':group,'endpoint':e,'condition':cond,'n':16,
                    **{f:{'true':sum(r[f] is True for r in rows),'false':sum(r[f] is False for r in rows),'uncertain':sum(r[f] is None for r in rows)}for f in flags}})
    write(H/'results/reading-summary.json',{'scope':'Blind assistant descriptive assessment, not independent human validation or adoption gate','groups':stats,'rows':merged,
        'readingsSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}})
    print(json.dumps(stats,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
