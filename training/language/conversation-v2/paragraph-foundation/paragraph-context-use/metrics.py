"""Pure reporting math; never edits logits, masks, weights or decoder."""
import math,statistics,hashlib,json,gzip,struct,pathlib

def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb')as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
def input_hash(ids):return hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()
def summarize(values,gold):
 m=max(values);e=[math.exp(x-m)for x in values];z=sum(e);logZ=m+math.log(z);p=[v/z for v in e]
 def row(t):return dict(token=t,P=p[t],logP=values[t]-logZ,rank=1+sum(v>values[t]for v in values))
 order=sorted(range(len(values)),key=lambda t:(-values[t],t));H=-sum(q*math.log(q)for q in p if q)
 return dict(newline=row(16),mata=row(3749),gold=row(gold),argmax=order[0],top10=[row(t)for t in order[:10]],entropy_nats=H),p

def js(p,q):
 return .5*sum(a*math.log(2*a/(a+b))if a else 0 for a,b in zip(p,q))+.5*sum(b*math.log(2*b/(a+b))if b else 0 for a,b in zip(p,q))
def distribution(v):
 s=sorted(v);n=len(s)
 def quantile(q):
  x=(n-1)*q;i=int(x);return s[i]+(s[min(i+1,n-1)]-s[i])*(x-i)
 bins=[sum(x< -1 for x in v),sum(-1<=x<-.1 for x in v),sum(-.1<=x<=0 for x in v),sum(0<x<=.1 for x in v),sum(.1<x<=1 for x in v),sum(x>1 for x in v)]
 return dict(values=v,n=n,positive=sum(x>0 for x in v),zero=sum(x==0 for x in v),negative=sum(x<0 for x in v),mean=statistics.mean(v),median=statistics.median(v),min=s[0],q25=quantile(.25),q75=quantile(.75),max=s[-1],near_zero_abs_le_01=sum(abs(x)<=.01 for x in v),bins=bins)
def aggregate(rows):
 out={}
 for group in ['balanced_all32','mata','other']:
  r=[x for x in rows if group=='balanced_all32'or x['group']==group]
  if not r:continue
  def mean(fn):return statistics.mean(fn(x)for x in r)
  out[group]=dict(n=len(r),delta=distribution([x['delta']for x in r]),
   P_LF=dict(C=mean(lambda x:x['C']['newline']['P']),U=mean(lambda x:x['U']['newline']['P']),C_minus_U=mean(lambda x:x['C']['newline']['P']-x['U']['newline']['P'])),
   P_mata=dict(C=mean(lambda x:x['C']['mata']['P']),U=mean(lambda x:x['U']['mata']['P']),C_minus_U=mean(lambda x:x['C']['mata']['P']-x['U']['mata']['P'])),
   P_gold=dict(C=mean(lambda x:x['C']['gold']['P']),U=mean(lambda x:x['U']['gold']['P'])),
   gold_rank=dict(C=mean(lambda x:x['C']['gold']['rank']),U=mean(lambda x:x['U']['gold']['rank']),rank_improved=sum(x['C']['gold']['rank']<x['U']['gold']['rank']for x in r)),
   argmax_changed=sum(x['C']['argmax']!=x['U']['argmax']for x in r),LF_argmax_C=sum(x['C']['argmax']==16 for x in r),LF_argmax_U=sum(x['U']['argmax']==16 for x in r),
   entropy=dict(C=mean(lambda x:x['C']['entropy_nats']),U=mean(lambda x:x['U']['entropy_nats']),C_minus_U=mean(lambda x:x['C']['entropy_nats']-x['U']['entropy_nats'])),
   mean_JS_nats=mean(lambda x:x['JS_nats']))
 return out

def teacher_input(history,tail):
 assert len(tail)==8 and len(history)+7<=256 and all(t>=6 for t in tail)
 return history+tail[:-1],list(range(len(history)-1,len(history)+7))
def archive_logits(path,rows):
 raw=b''.join(struct.pack('<%df'%len(r),*r)for r in rows)
 with pathlib.Path(path).open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0)as z:z.write(raw)
 return dict(file=pathlib.Path(path).name,shape=[len(rows),len(rows[0])],dtype='float32_little_endian',raw_sha256=hashlib.sha256(raw).hexdigest(),gzip_sha256=sha(path),bytes=len(raw))
