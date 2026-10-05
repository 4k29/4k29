"""Disclose old own QA model's exposure to the new raw-generation probes.

The new raw experiments have document-disjoint TEST. The historical owner
model used a different earlier split; its scores are not an equally unseen
comparison. No generation or new weights are produced here.
"""
import collections,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def main():
    corpus_path=ROOT.parent/'dialogue'/'switch-corpus.json';corpus=read(corpus_path)
    texts={};tok=corpus['tokenizer']
    for key,partition in [('pretraining','train'),('pretrainingValidation','validation'),('pretrainingTest','test')]:
        rows=collections.defaultdict(list)
        for r in corpus[key]:rows[r['document']].extend(r['tokens'][r['prefixLength']:])
        for identity,tokens in rows.items():texts[identity]=(partition,b''.join(bytes.fromhex(tok['bytes'][t]) for t in tokens).decode('utf8'))
    old={r['url']:r for r in corpus['provenance']['documents']};policy=read(ROOT/'generation-policy.json');rows=[]
    for r in policy['probes']['test']:
        source=old.get(r['url']);identity=source['id'] if source else None
        matches=[identity for identity,(partition,text) in texts.items() if partition=='train' and r['prefix'] in text]
        rows.append(dict(id=r['id'],site=r['site'],url=r['url'],oldSourceDocument=identity,oldSourcePartition=source['partition'] if source else None,openingPresentInOldRawTrain=bool(matches),oldTrainMatches=matches))
    report=dict(oldCorpusSha256=hashlib.sha256(corpus_path.read_bytes()).hexdigest(),newPolicySha256=hashlib.sha256((ROOT/'generation-policy.json').read_bytes()).hexdigest(),rows=rows,total=len(rows),oldTrainOpeningMatches=sum(r['openingPresentInOldRawTrain'] for r in rows),oldTrainSourceMatches=sum(r['oldSourcePartition']=='train' for r in rows),note='Old owner/SFT model used a different historical raw-source split and can have seen these source pages/openings. Raw training streams are reconstructed from nonoverlapping supervised targets, not inferred from generated answers. This baseline is descriptive, not evidence that all22 openings were unseen by that old model. New raw experiments use their own document-group-disjoint split and train-only vocabulary.')
    (ROOT/'baseline-exposure.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['total','oldTrainOpeningMatches','oldTrainSourceMatches']}))
if __name__=='__main__':main()
