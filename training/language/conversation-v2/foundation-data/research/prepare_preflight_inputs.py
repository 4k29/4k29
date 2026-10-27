"""Prepare fixed TRAIN-only windows before any forward/backward audit."""
import argparse,copy,hashlib,json,pathlib,sys
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parents[1];REPO=HERE.parents[4]
sys.path.insert(0,str(BASE))
from core import open_tokens
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text())
def main(a):
    if a.output.exists():raise ValueError('Refuse fixed-input overwrite')
    data_path=BASE/'data/data.json';data=read(data_path);values,windows=open_tokens(data,'train')
    candidates=read(a.native_candidates)
    if candidates['tokenizerSha256']!=data['tokenizerSha256']:raise ValueError('Candidate tokenizer mismatch')
    selected=[];documents=set()
    ranked=sorted(enumerate(windows),key=lambda pair:hashlib.sha256(('foundation-pf-rp-v1|'+pair[1]['document']+'|'+str(pair[1]['offset'])).encode()).hexdigest())
    for index,w in ranked:
        if w['length']!=257 or w['document']in documents:continue
        documents.add(w['document']);seq=np.asarray(values[w['offset']:w['offset']+257],dtype=np.int64).tolist()
        selected.append(dict(id='rp-window-'+str(index),documentId=w['document'],family=w['document'],partition='train',
            format='original-human-a-b',originalWindowIndex=index,tokenOffsetGlobal=w['offset'],
            sourceDataSha256=sha(data_path),sourceTokensSha256=data['trainTokensSha256'],tokens=seq))
        if len(selected)==8:break
    native=candidates['windows']
    if len(native)<4 or any(w['partition']!='train' or w['format']!='native-prose-bos-body-eos'for w in native):raise ValueError('Need four original final-split TRAIN prose windows')
    chosen=[]
    for source,quota in [('jaquad',2),('jawikibooks',1),('jawikivoyage',1)]:
        group=sorted([w for w in native if w['source']==source],key=lambda w:hashlib.sha256(('foundation-pf-prose-v1|'+w['id']).encode()).hexdigest())
        if len(group)<quota:raise ValueError('Missing fixed source-balanced audit quota: '+source)
        chosen.extend(group[:quota])
    native=chosen
    if len({w['documentId']for w in native})!=4:raise ValueError('Audit requires four different source documents')
    conditions={'control':[],'dataadd':[]}
    for i in range(2):
        control=selected[4*i:4*i+4];treatment=copy.deepcopy(control[:2])+native[2*i:2*i+2]
        conditions['control'].append(control);conditions['dataadd'].append(treatment)
    bundle=dict(scope='Fixed two paired batches per condition; gradient audit only, not admitted training dataset',
        actualOptimizerUpdates=0,tokenizerSha256=data['tokenizerSha256'],oldDataSha256=sha(data_path),
        nativeCandidateManifestSha256=sha(a.native_candidates),conditions=conditions,
        selectionRules=dict(rp='SHA256(foundation-pf-rp-v1|document|globaltokenoffset), first8 full windows with distinct documents',
            prose='Within-source SHA256(foundation-pf-prose-v1|candidatewindowID), first2JaQuAD+first1Wikibooks+first1Wikivoyage; diagnostic quota, not training mixture'),
        sealedTestRead=False,sourceAdmissionImplied=False)
    a.output.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(inputsSha256=sha(a.output),batches=4,actualOptimizerUpdates=0)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native-candidates',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);main(p.parse_args())
