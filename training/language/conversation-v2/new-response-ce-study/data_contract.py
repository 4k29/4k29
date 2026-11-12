"""Own-vocabulary instruction contract and explicit research-start gate. No model dependencies."""
def object_spans(text):
 quote=escape=False;depth=0;start=None
 for i,c in enumerate(text):
  if quote:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c=='"':quote=False
  elif c=='"':quote=True
  elif c=='{':
   if depth==0:start=i
   depth+=1
  elif c=='}':
   depth-=1
   if depth<0:raise ValueError('Unbalanced object')
   if depth==0:yield start,i+1,text[start:i+1]
 if quote or depth:raise ValueError('Unterminated source object')
def serialize(encode,question,answer):
 t=[1,3]+encode(question)+[2,4];start=len(t);t+=encode(answer)+[2]
 if len(t)>257:raise ValueError('Complete input does not fit context256; no crop')
 return t,start
def masks(tokens,start):
 if not 2<=start<len(tokens)or tokens[0]!=1 or tokens[start-1]!=4 or tokens[-1]!=2 or 0 in tokens:raise ValueError('Invalid complete instruction contract')
 if len(tokens)>257:raise ValueError('Over context')
 a=[True]*(len(tokens)-1);b=[i>=start-1 for i in range(len(tokens)-1)]
 assert b[-1]and not b[start-2]
 return a,b
def start_reasons(s):
 reasons=[]
 for key in ['rights_training_confirmed','source_revision_confirmed','source_original_distribution_confirmed','input_and_mask_fixed','DEV_fixed','durable_checkpoint_storage_confirmed','schedule_fixed']:
  if not s.get(key):reasons.append(key)
 if s.get('verified_train_response_body_tokens',0)<10000:reasons.append('verified_response_body_below10000')
 if s.get('NC_data_used')and not s.get('private_model_storage_confirmed'):reasons.append('NC_model_publication_prohibited')
 return reasons
def pack_lists(rows):
 T=max(len(t)-1 for t,s in rows);out=[]
 for t,s in rows:
  a,b=masks(t,s);n=len(t)-1;out.append(dict(x=t[:-1]+[0]*(T-n),y=t[1:]+[-100]*(T-n),all_mask=a+[False]*(T-n),response_mask=b+[False]*(T-n),valid=n))
 return out
