"""Unmask independently fixed full-output judgments; never modifies reader labels."""
import json,pathlib,hashlib
HERE=pathlib.Path(__file__).resolve().parent
SINGLE=['grammaticalNaturalWhole','semanticAppropriateWhole','specificContentAppropriate','contextConsistent','genericOnly','harmfulRepetition','topicDrift','naturalTermination','compositeWhole']
EPISODE=['meaningfulWholeEpisode','contextConsistentWholeEpisode','harmfulCrossTurnRepetition','allTurnsNatural']
def read(p):return json.loads(p.read_text())
def counts(rows,fields):
    return dict(n=len(rows),**{f:dict(true=sum(r[f]is True for r in rows),false=sum(r[f]is False for r in rows),uncertain=sum(r[f]is None for r in rows))for f in fields})
def main():
    key=read(HERE/'blind-key.json');pack=read(HERE/'blind-pack.json');ids={r['blindId']for r in pack['rows']}
    assert len(ids)==240 and set(key)==ids
    by_reader={};records={}
    for name in ['primary','secondary']:
        path=HERE/f'blind-reading-{name}.json';data=read(path);rows=data['rows']
        assert len(rows)==240 and {r['blindId']for r in rows}==ids
        mapped=[]
        for row in rows:
            k=key[row['blindId']];fields=EPISODE if k['kind']=='selfplay'else SINGLE
            assert all(f in row and (row[f]is None or type(row[f])is bool)for f in fields),(name,row['blindId'])
            mapped.append(dict(**row,endpoint=k['endpoint'],caseId=k['caseId'],kind=k['kind']))
        records[name]={r['blindId']:r for r in mapped};groups={}
        for endpoint in sorted({r['endpoint']for r in mapped}):
            local=[r for r in mapped if r['endpoint']==endpoint]
            groups[endpoint]={
                'unified32':counts([r for r in local if r['kind']=='single'and r['caseId'].startswith('v2-dev-')],SINGLE),
                'content24':counts([r for r in local if r['kind']=='single'and r['caseId'].startswith('v2-content-dev-')],SINGLE),
                'selfplay':counts([r for r in local if r['kind']=='selfplay'],EPISODE)}
        signals={}
        for model in ['medium','small']:
            before=groups[model+'-512']['content24'];after=groups[model+'-epoch1']['content24']
            gain=after['specificContentAppropriate']['true']-before['specificContentAppropriate']['true']
            signals[model]=dict(contentGain=gain,minimumPredeclaredGain=4,
                harmfulRepetitionBefore=before['harmfulRepetition']['true'],harmfulRepetitionAfter=after['harmfulRepetition']['true'],
                passesLimitedResearchSignal=gain>=4 and after['harmfulRepetition']['true']<=before['harmfulRepetition']['true'],
                formalAdoption=False)
        by_reader[name]=dict(fileSha256=hashlib.sha256(path.read_bytes()).hexdigest(),groups=groups,researchSignals=signals)
    disagreement=[]
    for ident in sorted(ids):
        a=records['primary'][ident];b=records['secondary'][ident];fields=EPISODE if a['kind']=='selfplay'else SINGLE
        changed=[f for f in fields if a[f]!=b[f]]
        if changed:disagreement.append(dict(blindId=ident,endpoint=a['endpoint'],caseId=a['caseId'],fields=changed,primary={f:a[f]for f in changed},secondary={f:b[f]for f in changed}))
    result=dict(scope='Independent assistant full-reading labels; not native human formal evaluation',readers=by_reader,
        primaryDeclaredBeforeReading=True,allFullItemsReadPerReader=240,disagreementItems=len(disagreement),disagreements=disagreement,
        labelsEditedAfterUnmasking=False,sealedTestUsed=False,formalAdoption=False)
    (HERE/'blind-reading-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='disagreements'},ensure_ascii=False))
if __name__=='__main__':main()
