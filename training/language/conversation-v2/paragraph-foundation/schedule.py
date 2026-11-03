"""Equal genuine-target budgets; every original teacher position used at most once."""
import hashlib

def rank(s):return hashlib.sha256(('paragraph-distribution-v1|'+s).encode()).hexdigest()
def references(corpus,indices):
 refs=[]
 for index in indices:
  tokens=corpus[index]['tokens']
  for start in range(0,len(tokens)-1,256):refs.append(dict(record=index,start=start,length=min(257,len(tokens)-start)))
 return sorted(refs,key=lambda r:(r['length'],rank(corpus[r['record']]['id']+'|'+str(r['start']))))
def batches(corpus,refs,budget,batch_targets=1024):
 result=[];current=[];count=0;total=0
 for ref in refs:
  used=0;valid=ref['length']-1
  while used<valid and total<budget:
   n=min(valid-used,batch_targets-count,budget-total);assert n>0
   current.append(dict(record=ref['record'],start=ref['start']+used,length=n+1));count+=n;total+=n;used+=n
   if count==batch_targets:result.append(current);current=[];count=0
  if total==budget:break
 if current:result.append(current)
 assert total==budget
 full=[b for b in result if sum(r['length']-1 for r in b)==batch_targets];tail=[b for b in result if sum(r['length']-1 for r in b)<batch_targets]
 full.sort(key=lambda b:rank('|'.join(corpus[r['record']]['id']+':'+str(r['start'])for r in b)))
 return full+tail

def verify(corpus,bs):
 visited=set();counts=[];EOS=0;roles=0;maximum_padding=0
 for batch in bs:
  count=0;width=max(r['length']-1 for r in batch);maximum_padding=max(maximum_padding,width*len(batch))
  for r in batch:
   seq=corpus[r['record']]['tokens'][r['start']:r['start']+r['length']];assert len(seq)==r['length']and 2<=len(seq)<=257
   for j,t in enumerate(seq[1:],r['start']+1):
    key=(r['record'],j);assert key not in visited;visited.add(key);count+=1;EOS+=t==2;roles+=t in(3,4)
  counts.append(count)
 return dict(targets=sum(counts),target_counts=counts,EOS_targets=EOS,role_targets=roles,duplicate_teacher_positions=0,max_padded_positions=maximum_padding,visited_positions=len(visited))
