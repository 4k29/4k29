"""Separate untrained followup candidate: preserve each original256-window prefix.
No new teacher positions or fake EOS; prefix-only labels are masked.
"""
def row(corpus,ref):
 start=ref['start'];lost=start%256;begin=start-lost;seq=corpus[ref['record']]['tokens'][begin:start+ref['length']]
 assert 2<=len(seq)<=257
 inputs=seq[:-1];labels=[-100]*lost+seq[lost+1:]
 assert len(inputs)==len(labels)and [x for x in labels if x!=-100]==corpus[ref['record']]['tokens'][start+1:start+ref['length']]
 return inputs,labels,dict(original_window_start=begin,prefix_only_positions=lost,source_target_start=start+1,real_targets=ref['length']-1)

def pack(corpus,refs,torch):
 rows=[row(corpus,r)for r in refs];width=max(len(x)for x,_,_ in rows);x=torch.zeros((len(rows),width),dtype=torch.long);y=torch.full_like(x,-100)
 for i,(xx,yy,_)in enumerate(rows):x[i,:len(xx)]=torch.tensor(xx);y[i,:len(yy)]=torch.tensor(yy)
 return x,y,[meta for _,_,meta in rows]
