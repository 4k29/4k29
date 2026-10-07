"""Count exact long-paragraph connections before any new data is split."""
import collections,hashlib,json,pathlib,unicodedata
ROOT=pathlib.Path(__file__).resolve().parent;PARENT=ROOT.parent/'round8'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=[json.loads(x) for x in (PARENT/'documents.jsonl').read_text().splitlines()]
    new=[json.loads(x) for x in (ROOT/'documents.jsonl').read_text().splitlines()]
    part={r['document']:r['partition'] for r in read(PARENT/'split.json')['assignments']}
    parent={d['id']:d['id'] for d in old+new};first={};titles={};paragraphs=collections.Counter();newids={d['id'] for d in new}
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def connect(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    for d in old+new:
        key=unicodedata.normalize('NFKC','|'.join([d['site'],d.get('author',''),d['title']])).strip()
        if key in titles:connect(d['id'],titles[key])
        else:titles[key]=d['id']
        for text in {x.strip() for x in d['text'].splitlines() if len(x.strip())>=80}:
            if d['id'] in newids:paragraphs[text]+=1
            if text in first:connect(d['id'],first[text])
            else:first[text]=d['id']
    groups=collections.defaultdict(lambda:dict(oldPartitions=set(),newDocuments=[]))
    for d in old:groups[find(d['id'])]['oldPartitions'].add(part[d['id']])
    for d in new:groups[find(d['id'])]['newDocuments'].append(d['id'])
    rows=[];connections=collections.Counter()
    for key,g in sorted(groups.items()):
        if not g['newDocuments']:continue
        for p in g['oldPartitions']:connections[p]+=len(g['newDocuments'])
        rows.append(dict(group=key,newDocuments=g['newDocuments'],priorPartitions=sorted(g['oldPartitions']),mustNotBecomeNewTrain=bool(g['oldPartitions']-{'train'})))
    report=dict(minimumSharedParagraphCharacters=80,sourceDocumentsSha256=sha(ROOT/'documents.jsonl'),priorDocumentsSha256=sha(PARENT/'documents.jsonl'),priorSplitSha256=sha(PARENT/'split.json'),auditorSourceSha256=sha(pathlib.Path(__file__)),newDocuments=len(new),groupsWithNewDocuments=len(rows),newDocumentsConnectedToPriorPartitions=dict(connections),newDocumentsConnectedToPriorNonTrain=sum(len(r['newDocuments']) for r in rows if r['mustNotBecomeNewTrain']),uniqueLongParagraphs=len(paragraphs),longParagraphDocumentOccurrences=sum(paragraphs.values()),repeatedLongParagraphTypes=sum(n>1 for n in paragraphs.values()),partitionsAssigned=False,tokenizerFitted=False,optimizerUpdates=0,groups=rows,note='NFKC(site|author|title).strip and exact trimmed paragraphs of >=80 Unicode characters; same parent fold grouping. Canonical URL duplication was excluded during collection; fuzzy or shorter overlap is not measured. Groups connected to old non-TRAIN must be kept out of new TRAIN; mixed prior partitions require quarantine. This audit does not assign or train any partition.')
    (ROOT/'overlap-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['newDocuments','groupsWithNewDocuments','newDocumentsConnectedToPriorPartitions','newDocumentsConnectedToPriorNonTrain','uniqueLongParagraphs','repeatedLongParagraphTypes','optimizerUpdates']}),flush=True)
if __name__=='__main__':main()
