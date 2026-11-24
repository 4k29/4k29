"""Shared source-preserving inputs; only next-token teacher mask differs. Not a training runner."""
def make_pair(tokens,response_body_start):
 if not tokens or tokens[0]!=1 or tokens[-1]!=2:raise ValueError('True conversation BOS / target EOS required')
 if not 2<=response_body_start<len(tokens) or tokens[response_body_start-1]not in [3,4]:raise ValueError('Target role must precede response')
 if len(tokens)>257:raise ValueError('No silent left truncation')
 if any(t in [0,1,2,3,4,5] for t in tokens[response_body_start:-1]):raise ValueError('Response body includes structural tokens')
 x=tokens[:-1];y=tokens[1:]
 a=[True]*len(y);b=[i+1>=response_body_start for i in range(len(y))]
 assert sum(b)==len(tokens)-response_body_start
 return dict(input_ids=x,teacher_ids=y,attention_valid=[True]*len(x),all_ce_mask=a,response_ce_mask=b)
def padded_pair(tokens,response_body_start,width=256):
 p=make_pair(tokens,response_body_start)
 if len(p['input_ids'])>width:raise ValueError('Width smaller than input')
 n=width-len(p['input_ids'])
 return {k:v+([0]*n if k=='input_ids' else [-100]*n if k=='teacher_ids' else [False]*n)for k,v in p.items()}
def masked_ce(logits,teacher,mask):
 import torch
 valid=mask & teacher.ne(-100)
 if not bool(valid.any()):raise ValueError('No active response teacher: stop, do not renormalize silently')
 # Global active-token mean, never per-response averaging or compensating multiplier.
 return torch.nn.functional.cross_entropy(logits[valid].float(),teacher[valid],reduction='sum')/valid.sum()
