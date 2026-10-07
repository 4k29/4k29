"""Extend own glyph byte-BPE with locally updated short word pairs."""
from collections import Counter
import heapq,copy

def extend(token_sequences,parent,merges=512,max_piece_bytes=18,numeric_boundaries=False):
    """Own weighted BPE with local occurrence/count updates.

    Frequency ties and overlapping merges match fit() exactly. Optional numeric
    boundaries keep ASCII digits separate from units/words without injecting
    a vocabulary or reserving any answer. Only training text supplies counts.
    """
    vocabulary=[bytes.fromhex(b) for b in parent['bytes']]
    numeric=[bool(b) and all(48<=c<=57 for c in b) for b in vocabulary]
    sequences=Counter(tuple(tokens) for tokens in token_sequences)
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
    result=copy.deepcopy(parent)
    result.update(bytes=[piece.hex() for piece in vocabulary],merges=parent['merges']+rules,maxPieceBytes=max_piece_bytes,wordMerges=len(rules),note='Own glyph rules retained; short word pairs learned only from original TRAIN glyph streams. No dictionary, teacher text, external weights or tokenizer.')
    if numeric_boundaries:result['numericBoundaries']=True
    return result


def apply_rules(tokens,rules):
    """Same learned BPE rules, using adjacent-pair updates for long articles.

    Rank and original left position preserve the global rule order and its
    left-to-right handling of overlapping equal pairs. No outside tokenizer.
    """
    values=list(tokens)
    if not values:return []
    ranks={(a,b):(rank,c) for rank,(a,b,c) in enumerate(rules)}
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

