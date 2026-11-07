"""Stateless own-model inference metrics. No optimizer, repair or answer lookup."""
import math
import torch
from torch.nn import functional as F


def byte_payload(ids,pieces):
    raw=b''.join(pieces[t]for t in ids)
    try:text=raw.decode('utf8',errors='strict');valid=True
    except UnicodeDecodeError:text=None;valid=False
    return dict(rawBytesHex=raw.hex(),text=text,strictUtf8=valid,
        nonEosContainsSpecialTokens=any(t<6 for t in ids),
        decodePolicy='Exact bytes; strict UTF8 only; null if invalid; special IDs retained separately; no replacement or repair')


def token_scores(logits,gold,pieces):
    if logits.ndim!=2 or len(gold)!=len(logits) or not gold:raise ValueError('Nonempty matched logit/target rows required')
    if not bool(torch.isfinite(logits).all()):raise ValueError('Nonfinite logits')
    ids=torch.tensor(gold,dtype=torch.long)
    if bool(((ids<0)|(ids>=logits.shape[-1])).any()):raise ValueError('Invalid gold IDs')
    logp=F.log_softmax(logits.float(),dim=-1);best=logits.argmax(-1)
    rows=[]
    for j,t in enumerate(gold):
        rows.append(dict(position=j,token=t,kind='eos'if t==2 else'role'if t in [3,4]else'body'if t>=6 else'other-special',
            utf8Bytes=len(pieces[t]),nll=float(-logp[j,t]),top1=int(best[j]),goldIsTop1=int(best[j])==t,
            goldProbability=float(logp[j,t].exp())))
    return rows


def aggregate(rows):
    if not rows:return dict(tokens=0,utf8Bytes=0,nllSum=0.,nllPerToken=None,nllPerUtf8Byte=None,top1Rate=None)
    nll=sum(r['nll']for r in rows);nbytes=sum(r['utf8Bytes']for r in rows)
    return dict(tokens=len(rows),utf8Bytes=nbytes,nllSum=nll,nllPerToken=nll/len(rows),
        nllPerUtf8Byte=nll/nbytes if nbytes else None,top1Rate=sum(r['goldIsTop1']for r in rows)/len(rows))


def groups(rows):
    return {kind:aggregate([r for r in rows if r['kind']==kind])for kind in ['body','role','eos','other-special']}|{'all':aggregate(rows)}


@torch.inference_mode()
def window_scores(model,seq,pieces):
    if not 2<=len(seq)<=model.config['context']+1:raise ValueError('Window outside fixed context')
    x=torch.tensor([seq[:-1]],dtype=torch.long)
    rows=token_scores(model(x)[0],seq[1:],pieces)
    return dict(tokens=rows,metrics=groups(rows))


@torch.inference_mode()
def response_scores(model,prefix,gold,pieces):
    if not prefix or prefix[0]!=1 or not gold or any(t<6 for t in gold):raise ValueError('Require BOS prefix and ordinary body gold')
    if len(prefix)+len(gold)>model.config['context']:raise ValueError('Gold body+EOS score needs full history within context')
    all_logits=model(torch.tensor([prefix+gold],dtype=torch.long))[0]
    body_logits=all_logits[len(prefix)-1:len(prefix)-1+len(gold)]
    rows=token_scores(body_logits,gold,pieces)
    end=all_logits[-1];eos=token_scores(end.unsqueeze(0),[2],pieces)[0]
    eos['rank']=1+int((end>end[2]).sum())+int(((end==end[2])&(torch.arange(len(end))<2)).sum())
    return body_logits,dict(tokens=rows,body=aggregate(rows),eosAtGoldEnd=eos,
        eosExcludedFromBodyNll=True,humanReferenceNotUnique=True)


def repeated_gram(ids,n=4):
    seen={}
    for i in range(max(0,len(ids)-n+1)):
        gram=tuple(ids[i:i+n])
        if gram in seen:return dict(n=n,firstStart=seen[gram],repeatStart=i,completion=i+n-1,tokens=list(gram),meaning='Mechanical repetition, not semantic failure onset')
        seen[gram]=i
    return None


@torch.inference_mode()
def greedy(model,prefix,pieces,gold=None,tf_logits=None,max_new=192,tolerance=2e-4):
    if not prefix or prefix[0]!=1 or len(prefix)+max_new>model.config['context']:raise ValueError('Full fixed generation must fit; no crop/rolling')
    emitted=[];steps=[];same=True;first_departure=None;reference=[]
    for j in range(max_new):
        logits=model(torch.tensor([prefix+emitted],dtype=torch.long))[0,-1]
        if not bool(torch.isfinite(logits).all()):raise ValueError('Nonfinite generation logits')
        chosen=int(logits.argmax());gap=float((logits.topk(2).values[0]-logits.topk(2).values[1]));check=None
        # Reference metrics never influence selection or the fed history.
        if gold is not None and j<len(gold) and same and tf_logits is not None:
            error=float((logits-tf_logits[j]).abs().max());tf_best=int(tf_logits[j].argmax())
            check=dict(sameHistory=True,maxAbsoluteError=error,tolerance=tolerance,withinTolerance=error<=tolerance,
                tfArgmax=tf_best,sequentialArgmax=chosen,argmaxAgreement=tf_best==chosen)
            reference.append(check)
        if gold is not None and j<len(gold) and first_departure is None and chosen!=gold[j]:first_departure=j;same=False
        steps.append(dict(position=j,chosen=chosen,topTwoLogitGap=gap,reference=check));emitted.append(chosen)
        if chosen==2:break
    eos=emitted[-1]==2;body=emitted[:-1]if eos else emitted[:]
    return dict(tokensIncludingEos=emitted,nonEosTokens=body,eos=eos,
        stopReason='eos2-human-utterance-end'if eos else'fixed-max-new-tokens',maxNewTokens=max_new,
        firstGoldDeparturePosition=first_departure,firstGoldDepartureIsNotSemanticFailureOnset=True,
        generatedNonEosTokens=len(body),steps=steps,repeated4gram=repeated_gram(body,4),
        numericalReference=dict(comparedPositions=len(reference),maximumAbsoluteError=max((r['maxAbsoluteError']for r in reference),default=None),
            toleranceExceedances=sum(not r['withinTolerance']for r in reference),argmaxDisagreements=sum(not r['argmaxAgreement']for r in reference),
            scope='Raw Python FP32 same gold history only; no JS/export/hardware equivalence claim'),
        **byte_payload(body,pieces))


def fence(text):
    import re
    n=max([len(x.group())for x in re.finditer(r'`+',text)]+[0])+1
    marker='`'*max(n,3)
    return marker+'\n'+text+'\n'+marker
