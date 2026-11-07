"""Reuse only existing judgments after exact regenerated raw output equivalence."""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];old=ROOT.parent/'round20/execution'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=read(old/'new-validation.json');b=read(ROOT/'execution/old-validation.json');m=read(old/'new-manual.json')
assert m['generationSha256']==sha(old/'new-validation.json')
assert a['modelFileSha256']==b['modelFileSha256'] and a['maxNewTokens']==b['maxNewTokens']==192
for x,y in zip(a['rows'],b['rows'],strict=True):
 assert all(x[k]==y[k] for k in ['id','prefix','text','tokens','eos','validTokens','validUtf8','inputTokens']),x['id']
m['previousGenerationSha256']=m['generationSha256'];m['generationSha256']=sha(ROOT/'execution/old-validation.json');m['note']='Existing Round20 control manual judgments retained only after exact full raw output equality on regenerated same17 inputs; no changed output judged by stale score.'
(ROOT/'execution/old-manual.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print('17/17 old raw outputs match stored Round20 control judgments')
