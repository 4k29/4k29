"""Future candidate only: choose an existing true human turn end within original prefix.
Not imported or used by Round33. No model, RNG, new tokenization or positive labels.
"""
import bisect,hashlib,json
class HumanTurnPrefixSelector:
 def __init__(self,feature,tokenizer,train_info,min_tokens=8,max_tokens=32):
  if not 1<=min_tokens<=max_tokens:raise ValueError('Invalid prefix range')
  self.min_tokens=min_tokens;self.max_tokens=max_tokens;self.ends=feature['boundariesByUnit'];docs={d['id']:d for d in train_info['documents']if d['site']=='human-chat'}
  if set(self.ends)!=set(docs):raise ValueError('Human unit coverage differs')
  for key,ends in self.ends.items():
   if ends!=sorted(set(ends))or any(type(n)is not int or not 0<n<docs[key]['length']for n in ends):raise ValueError('Invalid true token ends')
  pieces=[bytes.fromhex(x)for x in tokenizer['bytes']];self.valid_start=[i==1 or (i>=6 and bool(b)and not 0x80<=b[0]<0xC0)for i,b in enumerate(pieces)]
 def length(self,row,first_token):
  if row['length']<2:raise ValueError('Require a true nonempty next target')
  base=min(self.max_tokens,row['length']-1)
  if row['site']!='human-chat':return base
  if row['unit']not in self.ends:raise ValueError('Unfrozen human source unit')
  if row['start']<0 or not 0<=first_token<len(self.valid_start):raise ValueError('Invalid source prefix')
  if not self.valid_start[first_token]:return base
  if first_token==1 and row['start']!=0:raise ValueError('BOS only at true unit start')
  ends=self.ends[row['unit']];j=bisect.bisect_right(ends,row['start']+base)-1
  if j>=0:
   n=ends[j]-row['start']
   if n>=self.min_tokens:return n
  return base

def load_selector(feature_path,tokenizer,train_info,expected_sha,tokenizer_sha,index_sha,source_documents_sha,min_tokens=8,max_tokens=32):
 raw=feature_path.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected_sha:raise ValueError('Frozen feature bytes changed')
 feature=json.loads(raw)
 for key,value in [('tokenizerSha256',tokenizer_sha),('trainIndexSha256',index_sha),('trainTokensSha256',train_info['tokensSha256']),('sourceDocumentsSha256',source_documents_sha)]:
  if feature[key]!=value:raise ValueError('Feature/source identity differs: '+key)
 return HumanTurnPrefixSelector(feature,tokenizer,train_info,min_tokens,max_tokens)
