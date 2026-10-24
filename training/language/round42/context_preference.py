"""Correct-context CE; mismatched context remains diagnostic only on frozen original human TRAIN utterances only."""
import hashlib,json,torch
from torch.nn import functional as F

def load_pool(path,expected_sha):
 raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected_sha
 pool=json.loads(raw);assert pool['partition'].startswith('TRAIN ONLY') and pool['trainingUpdates']==0
 rows=pool['rows'];assert rows
 for r in rows:
  assert r['document']!=r['wrongDocument'] and len(r['prefixTokens'])==len(r['wrongPrefixTokens'])
  assert 16<=len(r['prefixTokens'])<=96 and 12<=len(r['targetTokens'])<=96
  assert all(t>=6 for k in ['prefixTokens','wrongPrefixTokens','targetTokens'] for t in r[k])
 return rows

def preference_loss(model,pool,call_index,batch=2):
 """Same gold in both contexts, no generated positives; no stateful sampling."""
 assert call_index>=0 and batch>0
 selected=[pool[(call_index*batch+j)%len(pool)] for j in range(batch)]
 was_training=model.training
 try:
  # No stochastic context advantage; preserve the base CE dropout stream exactly.
  with torch.random.fork_rng(devices=[]):
   model.eval();examples=[]
   for r in selected:
    for key in ['prefixTokens','wrongPrefixTokens']:
     p=[1]+r[key];t=r['targetTokens'];examples.append((p+t, len(p),len(t)))
   width=max(len(seq)-1 for seq,_,_ in examples)
   assert width<=model.config['context']
   x=torch.zeros((len(examples),width),dtype=torch.long);y=torch.full_like(x,-100)
   for i,(seq,start,n) in enumerate(examples):
    x[i,:len(seq)-1]=torch.tensor(seq[:-1]);y[i,start-1:start-1+n]=torch.tensor(seq[start:])
   logits=model(x);ce=F.cross_entropy(logits.reshape(-1,model.config['vocabulary']),y.reshape(-1),reduction='none').reshape_as(y)
   means=ce.sum(-1)/y.ne(-100).sum(-1);correct=means[::2];wrong=means[1::2]
   loss=correct.mean()
   return loss,dict(pairs=batch,positiveTargetTokens=sum(len(r['targetTokens']) for r in selected),scoredTargetTokensBothContexts=2*sum(len(r['targetTokens']) for r in selected),inputTokensBothContexts=sum(2*(1+len(r['prefixTokens'])+len(r['targetTokens'])-1) for r in selected),meanCorrectNll=float(correct.detach().mean()),meanMismatchedNll=float(wrong.detach().mean()),meanContextGain=float((wrong-correct).detach().mean()),firstPoolIndex=(call_index*batch)%len(pool))
 finally:model.train(was_training)
