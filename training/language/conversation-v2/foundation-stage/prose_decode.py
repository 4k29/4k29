"""Same full-vocabulary greedy; permit planned BOS-free source fragments. No padding or fabricated BOS."""
import torch
from eval_core import byte_payload,repeated_gram

@torch.inference_mode()
def greedy(model,prefix,pieces,gold=None,tf_logits=None,max_new=192,tolerance=2e-4):
    if not prefix or len(prefix)+max_new>model.config['context']:raise ValueError('Full fixed generation must fit; no crop/rolling')
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

