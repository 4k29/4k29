"""Own byte-level BPE. No external tokenizer files or learned vocabulary.

Vocabulary and merges are fitted on training strings only. Limiting pieces to
12 bytes prevents frequent complete answers becoming a single answer token.
"""
from collections import Counter
import heapq
import unicodedata

SPECIALS = {'pad': 0, 'bos': 1, 'eos': 2, 'user': 3, 'assistant': 4, 'turn': 5}


def fit(texts, merges=384, max_piece_bytes=12):
    vocabulary = [b''] * len(SPECIALS) + [bytes([i]) for i in range(256)]
    sequences = Counter(tuple(byte+len(SPECIALS) for byte in text.encode('utf-8')) for text in texts)
    rules = []
    for _ in range(merges):
        counts = Counter()
        for tokens, weight in sequences.items():
            for pair in zip(tokens, tokens[1:]):
                if len(vocabulary[pair[0]])+len(vocabulary[pair[1]]) <= max_piece_bytes:
                    counts[pair] += weight
        if not counts:
            break
        pair, frequency = min(counts.items(), key=lambda item: (-item[1], item[0]))
        if frequency < 2:
            break
        token = len(vocabulary)
        vocabulary.append(vocabulary[pair[0]]+vocabulary[pair[1]])
        rules.append([*pair, token])
        updated = Counter()
        for tokens, weight in sequences.items():
            updated[tuple(merge(tokens, pair, token))] += weight
        sequences = updated
    return dict(schemaVersion=1, specials=SPECIALS, bytes=[piece.hex() for piece in vocabulary], merges=rules, maxPieceBytes=max_piece_bytes, note='Fitted on training strings only; no external tokenizer or vocabulary.')


def fit_fast(texts,merges=384,max_piece_bytes=12,numeric_boundaries=False):
    """Own weighted BPE with local occurrence/count updates.

    Frequency ties and overlapping merges match fit() exactly. Optional numeric
    boundaries keep ASCII digits separate from units/words without injecting
    a vocabulary or reserving any answer. Only training text supplies counts.
    """
    vocabulary=[b'']*len(SPECIALS)+[bytes([i]) for i in range(256)]
    numeric=[False]*len(SPECIALS)+[48<=i<=57 for i in range(256)]
    sequences=Counter(tuple(byte+len(SPECIALS) for byte in text.encode('utf-8')) for text in texts)
    values=[];previous=[];following=[];weights=[]
    for sequence,weight in sequences.items():
        start=len(values);values.extend(sequence);weights.extend([weight]*len(sequence))
        previous.extend([-1]+list(range(start,start+len(sequence)-1)) if sequence else [])
        following.extend(list(range(start+1,start+len(sequence)))+[-1] if sequence else [])
    alive=[True]*len(values);occurrences={};counts=Counter();dirty=set()
    def pair_at(left):
        if left<0 or not alive[left]:return None
        right=following[left]
        if right<0:return None
        a,b=values[left],values[right]
        if len(vocabulary[a])+len(vocabulary[b])>max_piece_bytes:return None
        if numeric_boundaries and numeric[a]!=numeric[b]:return None
        return a,b
    def add(left):
        pair=pair_at(left)
        if pair is None:return
        occurrences.setdefault(pair,set()).add(left);counts[pair]+=weights[left];dirty.add(pair)
    def remove(left):
        pair=pair_at(left)
        if pair is None:return
        occurrences[pair].remove(left);counts[pair]-=weights[left];dirty.add(pair)
    for left in range(len(values)):add(left)
    queue=[(-frequency,*pair) for pair,frequency in counts.items() if frequency>=2]
    heapq.heapify(queue);dirty.clear();rules=[]
    for _ in range(merges):
        while queue:
            negative,a,b=heapq.heappop(queue)
            if counts[(a,b)]==-negative:break
        else:break
        token=len(vocabulary);vocabulary.append(vocabulary[a]+vocabulary[b]);numeric.append(numeric[a] and numeric[b])
        rules.append([a,b,token])
        for left in sorted(occurrences[(a,b)]):
            if pair_at(left)!=(a,b):continue
            right=following[left];before=previous[left];after=following[right]
            remove(before);remove(left);remove(right)
            values[left]=token;alive[right]=False;following[left]=after
            if after>=0:previous[after]=left
            add(before);add(left)
        for pair in dirty:
            if counts[pair]>=2:heapq.heappush(queue,(-counts[pair],*pair))
        dirty.clear()
        if len(queue)>4*max(1,len(counts)):
            queue=[(-frequency,*pair) for pair,frequency in counts.items() if frequency>=2];heapq.heapify(queue)
    result=dict(schemaVersion=1,specials=SPECIALS,bytes=[piece.hex() for piece in vocabulary],merges=rules,maxPieceBytes=max_piece_bytes,note='Fitted on training strings only; no external tokenizer or vocabulary.')
    if numeric_boundaries:result['numericBoundaries']=True
    return result


def merge(tokens, pair, token):
    result, index = [], 0
    while index < len(tokens):
        if index+1 < len(tokens) and (tokens[index], tokens[index+1]) == tuple(pair):
            result.append(token)
            index += 2
        else:
            result.append(tokens[index])
            index += 1
    return result


def encode(text, tokenizer):
    tokens = [byte+len(SPECIALS) for byte in text.encode('utf-8')]
    for left, right, token in tokenizer['merges']:
        tokens = merge(tokens, (left, right), token)
    return tokens


def encode_stream(text,tokenizer):
    """Same learned BPE rules, using adjacent-pair updates for long articles.

    Rank and original left position preserve the global rule order and its
    left-to-right handling of overlapping equal pairs. No outside tokenizer.
    """
    values=[byte+len(SPECIALS) for byte in text.encode('utf-8')]
    if not values:return []
    ranks={(a,b):(rank,c) for rank,(a,b,c) in enumerate(tokenizer['merges'])}
    previous=list(range(-1,len(values)-1));following=list(range(1,len(values)))+[-1]
    alive=[True]*len(values);queue=[]
    def enqueue(left):
        if left<0 or not alive[left]:return
        right=following[left]
        if right<0:return
        pair=(values[left],values[right])
        if pair in ranks:
            rank,result=ranks[pair];heapq.heappush(queue,(rank,left,right,*pair,result))
    for index in range(len(values)-1):enqueue(index)
    while queue:
        _,left,right,a,b,result=heapq.heappop(queue)
        if not alive[left] or not alive[right] or following[left]!=right or values[left]!=a or values[right]!=b:continue
        values[left]=result;alive[right]=False;following[left]=following[right]
        if following[right]>=0:previous[following[right]]=left
        enqueue(previous[left]);enqueue(left)
    return [value for value,keep in zip(values,alive) if keep]


def decode(tokens, tokenizer):
    return b''.join(bytes.fromhex(tokenizer['bytes'][token]) for token in tokens).decode('utf-8', errors='replace')


def prompt(question, history, tokenizer):
    normalize=lambda q:unicodedata.normalize('NFKC',q).lower()
    result = [SPECIALS['bos']]
    for turn in history:
        result += [SPECIALS['user']] + encode(normalize(turn['question']), tokenizer)
        result += [SPECIALS['assistant']] + encode(turn['answer'], tokenizer) + [SPECIALS['turn']]
    return result + [SPECIALS['user']] + encode(normalize(question), tokenizer) + [SPECIALS['assistant']]
