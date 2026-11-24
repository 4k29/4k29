"""Fixed-checkpoint inference diagnostics. No optimizers, training, or repair.

Functions accept any deterministic causal model; toy tests never load own weights.
"""
import hashlib
import math
import re

import torch
from torch.nn import functional as F


def score_positions(logits, gold):
    if logits.ndim != 2 or len(gold) != logits.shape[0] or not gold:
        raise ValueError('Require one nonempty gold ID per logit row')
    targets = torch.tensor(gold, dtype=torch.long, device=logits.device)
    if bool(((targets < 0) | (targets >= logits.shape[1])).any()) or not bool(torch.isfinite(logits).all()):
        raise ValueError('Invalid gold IDs or nonfinite logits')
    logp = F.log_softmax(logits.float(), dim=-1)
    rows = []
    ids = torch.arange(logits.shape[1], device=logits.device)
    for j, token in enumerate(gold):
        values = logits[j]
        best = int(values.argmax())
        rank = 1 + int((values > values[token]).sum()) + int(((values == values[token]) & (ids < token)).sum())
        others = values.clone(); others[token] = -torch.inf
        rows.append({'position': j, 'goldToken': token, 'nll': float(-logp[j, token]),
                     'goldRank': rank, 'top1Token': best, 'goldIsTop1': best == token,
                     'goldProbability': float(logp[j, token].exp()),
                     'goldMinusBestOtherLogit': float(values[token] - others.max())})
    return rows


def aggregate(rows):
    if not rows:
        return {'tokens': 0, 'meanNll': None, 'meanGoldRank': None, 'top1Rate': None,
                'meanGoldProbability': None, 'meanGoldMinusBestOtherLogit': None}
    n = len(rows)
    return {'tokens': n, 'meanNll': sum(r['nll'] for r in rows)/n,
            'meanGoldRank': sum(r['goldRank'] for r in rows)/n,
            'top1Rate': sum(r['goldIsTop1'] for r in rows)/n,
            'meanGoldProbability': sum(r['goldProbability'] for r in rows)/n,
            'meanGoldMinusBestOtherLogit': sum(r['goldMinusBestOtherLogit'] for r in rows)/n}


def byte_payload(tokens, pieces):
    raw = b''.join(pieces[token] for token in tokens)
    try:
        text = raw.decode('utf-8', errors='strict')
        valid = True
    except UnicodeDecodeError:
        text = None; valid = False
    return {'rawBytesHex': raw.hex(), 'strictUtf8': valid, 'text': text,
            'textPolicy': 'Strict UTF8 only; null when invalid; never replacement decoding or output repair'}


@torch.inference_mode()
def teacher_forced(model, prefix, gold, eos=2):
    if not prefix or not gold or prefix[0] != 1 or eos in gold:
        raise ValueError('Require BOS prefix and nonempty gold without EOS')
    if len(prefix)+len(gold) > model.config['context']:
        raise ValueError('TF exceeds context; no truncation permitted')
    inputs = torch.tensor([prefix+gold], dtype=torch.long)
    all_logits = model(inputs)[0]
    start = len(prefix)-1
    scored = all_logits[start:start+len(gold)]
    end = all_logits[start+len(gold)]
    eos_score = score_positions(end.unsqueeze(0), [eos])[0]
    return scored, {'tokens': score_positions(scored, gold),
                    'eosAtGoldEnd': {'probability': eos_score['goldProbability'],
                        'rank': eos_score['goldRank'], 'isTop1': eos_score['goldIsTop1'],
                        'nll': eos_score['nll'], 'excludedFromGoldTokenMetrics': True}}


@torch.inference_mode()
def greedy(model, prefix, gold, tf_logits, pieces, max_new=192, eos=2, reference_tolerance=2e-4):
    if not 1 <= len(prefix) <= 64 or prefix[0] != 1:
        raise ValueError('Diagnostic prefixes must contain BOS and at most64 tokens')
    if len(prefix)+max_new > model.config['context']:
        raise ValueError('Requested generation exceeds context; no truncation/rolling window')
    emitted = []; trace = []; same_gold_history = True; first_departure = None
    terminated = False
    for j in range(max_new):
        logits = model(torch.tensor([prefix+emitted], dtype=torch.long))[0,-1]
        if not bool(torch.isfinite(logits).all()): raise ValueError('Nonfinite generation logits')
        chosen = int(logits.argmax())  # Full vocabulary; first ID wins exact ties.
        logp = F.log_softmax(logits.float(), dim=-1)
        top2 = logits.topk(2).values
        row = {'position': j, 'chosenToken': chosen,
               'chosenProbability': float(logp[chosen].exp()),
               'topTwoLogitGap': float(top2[0]-top2[1]),
               'referenceComparison': None}
        if j < len(gold) and same_gold_history:
            reference = tf_logits[j]
            error = float((logits-reference).abs().max())
            tf_best = int(reference.argmax())
            row['referenceComparison'] = {'sameGoldHistoryBeforePrediction': True,
                'teacherForcedArgmax': tf_best, 'actualGreedyArgmax': chosen,
                'argmaxAgreement': tf_best == chosen,
                'maximumAbsoluteLogitError': error, 'referenceTolerance': reference_tolerance,
                'withinReferenceTolerance': error <= reference_tolerance,
                'teacherForcedTopTwoGap': float(reference.topk(2).values[0]-reference.topk(2).values[1])}
        if j < len(gold) and chosen != gold[j] and first_departure is None:
            first_departure = j
            same_gold_history = False
        emitted.append(chosen); trace.append(row)
        if chosen == eos:
            terminated = True
            break
    non_eos = emitted[:-1] if terminated else emitted[:]
    references = [row['referenceComparison'] for row in trace if row['referenceComparison'] is not None]
    return {'tokensIncludingEos': emitted, 'nonEosTokens': non_eos,
            'eos': terminated, 'generatedNonEosTokens': len(non_eos),
            'stopReason': 'eos' if terminated else 'fixed-max-new-tokens',
            'maxNewTokens': max_new, 'firstGoldDeparturePosition': first_departure,
            'firstDepartureDefinition': 'First generated ID differing from gold at an available gold position, including premature EOS',
            'steps': trace, 'tokenPolicy': 'Full-vocabulary greedy; no filters, penalties, special-token suppression, rolling context or repair',
            'nonEosContainsSpecialTokens': any(t < 6 for t in non_eos),
            'numericalReference': {'comparedPositions': len(references),
                'argmaxDisagreements': sum(not r['argmaxAgreement'] for r in references),
                'toleranceExceedances': sum(not r['withinReferenceTolerance'] for r in references),
                'maxAbsoluteLogitError': max((r['maximumAbsoluteLogitError'] for r in references), default=None),
                'scope': 'TF batched-history vs sequential raw Python FP32, only while identical preceding history; includes departure prediction; no JS claim'},
            **byte_payload(non_eos, pieces)}


@torch.inference_mode()
def generated_history_probe(model, prefix, gold, generation, tf_rows):
    generated = generation['nonEosTokens']
    k = min(len(gold), len(generated)+(1 if generation['eos'] else 0))
    if k < 1: raise ValueError('Expected at least one generated prediction')
    # Exactly one causal forward. Never include EOS or any generated ID beyond
    # the preceding history of the final probed position.
    inputs = prefix+generated[:k-1]
    if 2 in generated or len(inputs) > model.config['context']:
        raise ValueError('Generated history contains EOS or exceeds context')
    logits = model(torch.tensor([inputs], dtype=torch.long))[0]
    scores = score_positions(logits[len(prefix)-1:len(prefix)-1+k], gold[:k])
    departure = generation['firstGoldDeparturePosition']
    rows = []
    for j, row in enumerate(scores):
        if departure is None or j < departure: region = 'before-departure'
        elif j == departure: region = 'at-departure'
        else: region = 'after-departure'
        rows.append({**row, 'region': region, 'teacherForced': tf_rows[j],
                     'nllDifferenceFromTeacherForced': row['nll']-tf_rows[j]['nll']})
    grouped = {region: aggregate([r for r in rows if r['region'] == region])
               for region in ['before-departure','at-departure','after-departure']}
    return {'K': k, 'rows': rows, 'byDepartureRegion': grouped,
            'sameIndicesTeacherForced': aggregate(tf_rows[:k]),
            'generatedHistoryGoldScores': aggregate(scores),
            'fedGeneratedTokenCount': k-1, 'fedEos': False,
            'interpretation': 'Counterfactual sensitivity of the SAME gold y_j to generated preceding IDs. After departure the gold is not an aligned language-accuracy reference.',
            'regionDefinition': 'Strictly before / exactly at / strictly after first ID departure. At departure, preceding histories are still identical.'}


def content_spans(text, gold, pieces, spans, tf_rows):
    raw = b''.join(pieces[t] for t in gold)
    if raw != text.encode('utf-8'): raise ValueError('Gold token bytes do not reconstruct exact targetText')
    offsets = [0]
    for token in gold: offsets.append(offsets[-1]+len(pieces[token]))
    results = []
    for span in spans:
        start, end = span['startCharacter'], span['endCharacter']
        if not 0 <= start < end <= len(text) or text[start:end] != span['text']:
            raise ValueError('Manual content span does not match exact target character offsets')
        a, b = len(text[:start].encode('utf-8')), len(text[:end].encode('utf-8'))
        touched = [j for j in range(len(gold)) if offsets[j] < b and offsets[j+1] > a]
        aligned = [j for j in touched if a <= offsets[j] and offsets[j+1] <= b]
        full = a in offsets and b in offsets
        results.append({**span, 'startUtf8Byte': a, 'endUtf8Byte': b,
            'fullyTokenAligned': full, 'touchedTokenPositions': touched,
            'fullyContainedTokenPositions': aligned,
            'touchedTokenScores': [tf_rows[j] for j in touched],
            'fullyContainedTokenScores': [tf_rows[j] for j in aligned],
            'wholeSpanTeacherTop1Exact': all(tf_rows[j]['goldIsTop1'] for j in touched) if full else None,
            'wholeSpanExactPolicy': 'Only defined when both span endpoints align to original token boundaries; manual labels, no POS model',
            'touchedSummary': aggregate([tf_rows[j] for j in touched]),
            'fullyContainedSummary': aggregate([tf_rows[j] for j in aligned])})
    return results


def repeated_ngram_onset(tokens, n=4):
    seen = {}
    for start in range(max(0,len(tokens)-n+1)):
        gram = tuple(tokens[start:start+n])
        if gram in seen:
            return {'ngram': n, 'repeatedStartPosition': start,
                    'repeatCompletionPosition': start+n-1,
                    'firstOccurrenceStartPosition': seen[gram], 'tokens': list(gram),
                    'interpretation': 'Mechanical exact repeated-token ngram; not semantic quality-degradation onset'}
        seen[gram] = start
    return None


def macro_and_token_weighted(cases):
    """Both target-length weighted and equal-case macro; never pool source splits."""
    summaries = [aggregate(rows) for rows in cases if rows]
    token = aggregate([row for rows in cases for row in rows])
    names = ['meanNll','meanGoldRank','top1Rate','meanGoldProbability','meanGoldMinusBestOtherLogit']
    macro = {name: sum(r[name] for r in summaries)/len(summaries) if summaries else None for name in names}
    return {'cases': len(summaries), 'equalCaseMacro': macro, 'tokenWeighted': token}


def fence(text):
    longest = max((len(m.group()) for m in re.finditer(r'`+', text)), default=0)
    delimiter = '`' * max(3,longest+1)
    return delimiter+'text\n'+text+'\n'+delimiter
