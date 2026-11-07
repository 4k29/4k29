"""Unblind completed saved readings; keep all original reviewer disagreements."""
import json,pathlib
H=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
    root=H/'evaluation';keys={r['blindId']:r for r in read(root/'blind-key.json')}
    raw={r['blindId']:r for r in read(root/'blind-input.json')}
    sources={'evaluation':read(root/'blind-reading-eval.json'),'model':read(root/'blind-reading-model.json')}
    fields=['naturalWhole','meaningfulWhole','appropriateWhole','specificContentAppropriate','genericOnly','harmfulRepetition','topicDrift','contextConsistency','naturalTermination','compositeWhole']
    merged={name:[{**r,**keys[r['blindId']]}for r in source['rows']]for name,source in sources.items()}
    assert len(merged['evaluation'])==87 and len(merged['model'])==64
    assert all(r['readComplete'] for rows in merged.values()for r in rows)
    stats=[]
    for reviewer,rs in merged.items():
        for endpoint in ['small','medium','r46']:
            rows=[r for r in rs if r['endpoint']==endpoint]
            if not rows:continue
            for cohort,subset in [('all-supported',rows),('paired23',[r for r in rows if r['paired23']]),('content-required',[r for r in rows if raw[r['blindId']]['contentRequired']])]:
                stats.append({'reviewer':reviewer,'endpoint':endpoint,'cohort':cohort,'n':len(subset),
                    **{f:{'true':sum(r[f] is True for r in subset),'false':sum(r[f] is False for r in subset),'uncertain':sum(r[f] is None for r in subset)}for f in fields}})
    agreement=[];a={r['blindId']:r for r in merged['evaluation']};b={r['blindId']:r for r in merged['model']}
    for f in fields:
        agreement.append({'field':f,'rows':64,'exactAgreement':sum(a[i][f]==b[i][f]for i in b),
            'definitionComparable':f!='naturalTermination','caution':'Evaluation uses semantically appropriate full end; Model uses syntactic/EOS end. Do not pool this axis.' if f=='naturalTermination' else None})
    eps=read(root/'blind-selfplay-reading.json')['rows'];epkeys={r['blindId']:r for r in read(root/'blind-selfplay-key.json')}
    selfplay=[]
    for name in ['small','medium']:
        rows=[r for r in eps if epkeys[r['blindId']]['endpoint']==name]
        selfplay.append({'endpoint':name,'episodes':len(rows),'meaningfulEpisodes':sum(r['episodeMeaningful'] is True for r in rows),
            'compositeEpisodes':sum(r['compositeWhole'] is True for r in rows),'crossTurnHarmfulRepetition':sum(r['harmfulRepetition'] is True for r in rows),
            'all3TurnsTerminated':sum(r['all3TurnsNaturallyTerminated'] is True for r in rows),
            'scope':'Own A/B selfplay only, not human-interactive response'})
    write(root/'reading-summary.json',{'groups':stats,'agreement':agreement,'selfplay':selfplay,
        'primaryReviewer':'evaluation uses the same frozen rubric over all87; other reviewer independent confirmation over new64',
        'terminationDefinitionDisagreementRetained':True,'capabilityNotProvedByAcknowledgementOnlyComposite':True,
        'humanNativeIndependentEvaluation':False})
    print(json.dumps({'groups':stats,'selfplay':selfplay},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
