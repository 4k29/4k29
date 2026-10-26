"""Independent output inventory and byte/token/source integrity audit."""
import json,pathlib,hashlib
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parent
read=lambda p:json.loads(p.read_text())
def main():
 pieces=[bytes.fromhex(x)for x in read(BASE/'data/tokenizer.json')['bytes']];panels=read(HERE/'unified32-dev.json')['cases']+read(HERE/'content-dev.json')['cases'];cases={c['id']:c for c in panels};reports=[]
 for out in sorted((HERE/'evaluation').iterdir()):
  if not(out/'receipt.json').exists():continue
  g=read(out/'generations.json');tf=read(out/'response-tf.json');roll=read(out/'selfplay.json');r=read(out/'receipt.json');w=read(out/'window-tf.json')
  assert len(g)==len(tf)==56 and set(x['id']for x in g)==set(cases)and len(w)==64 and len(roll)==4
  for x in g:
   c=cases[x['id']];assert x['prefixTokens']==c['prefixTokens']and x['originalPrefixTokens']==c['originalPrefixTokens'];assert [t for t in x['prefixTokens']if t not in(3,4)]==[t for t in x['originalPrefixTokens']if t not in(3,4)]
   assert b''.join(pieces[t]for t in x['goldTokens'])==c['targetText'].encode();raw=b''.join(pieces[t]for t in x['nonEosTokens']);assert raw.hex()==x['rawBytesHex'];assert x['eos']==(x['tokensIncludingEos'][-1]==2)
   if x['strictUtf8']:assert raw.decode('utf8')==x['text']
  for ep in roll:
   for row in ep['rows']:
    assert row['inputTokens'][:2]==[1,3];assert len(row['inputTokens'])+64<=256
    z=row['generation'];assert b''.join(pieces[t]for t in z['nonEosTokens']).hex()==z['rawBytesHex']
  assert r['modelAndRngUnchanged']and r['optimizerUpdates']==0 and not r['sealedTestUsed']
  reports.append(dict(endpoint=out.name,singleOutputs=56,teacherForcedResponses=56,packedDevWindows=64,selfplayEpisodes=4,selfplayTurns=sum(len(ep['rows'])for ep in roll),byteAndTokenIntegrity=True,bodyEosOrderPreserved=True,bosRole3AllPrefixes=True,noInferenceUpdates=True))
 report=dict(passed=True,endpoints=reports,sealedTestRead=False,scope='Artifact integrity, not semantic language capability');(HERE/'evaluation-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
