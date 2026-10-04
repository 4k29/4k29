"""Continuous document next-token targets without invented mid-sentence EOS."""
from tokenizer import SPECIALS,encode_stream

def windows(text,tokenizer,document,maximum_input=128,lookback=16):
    if not 1<=lookback<maximum_input:raise ValueError('Invalid lookback/input width')
    full=[SPECIALS['bos']]+encode_stream(text,tokenizer)+[SPECIALS['eos']]
    rows=[];start=0
    while start<len(full)-1:
        end=min(start+maximum_input+1,len(full))
        prefix=1 if start==0 else lookback
        rows.append(dict(document=document,start=start,end=end,prefixLength=prefix,tokens=full[start:end]))
        if end==len(full):break
        start=end-lookback
    return rows
