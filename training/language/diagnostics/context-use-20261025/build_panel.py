"""Build a fixed authentic TRAIN/exposed-DEV diagnostic panel; no model imports."""
import hashlib,json,pathlib,sys
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'training/dialogue'))
from tokenizer import encode_stream
OUT=pathlib.Path(__file__).resolve().parent
R=ROOT/'training/language/round46'; R47=ROOT/'training/language/round47'; PRE=ROOT/'training/language/round48-preflight'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def read(p):return json.loads(p.read_text())
def rel(p):return str(p.relative_to(ROOT))
# Manual input-validity review before any model outputs; never score-based.
DONOR_EXCLUSIONS={
 ('content-native-07','realpersona:11212',13):'Still food/noodles (そうめん) versus pasta',
 ('train-realpersona-01','realpersona:03913',4):'Shared food topic: Korean food versus ramen',
 ('content-native-07','realpersona:03073',21):'Shared pasta/ramen topic versus pasta',
 ('fresh-mrmp-01','realpersona:05907',18):'Shared baby/childcare topic: baby food versus baby',
}
def main():
 audit={'schemaVersion':1,'modelInstantiated':False,'optimizerUpdates':0,'reservedTestRead':False,'failures':[],'preOutputManualDonorExclusions':[]}
 try:
  tokpath=R/'multiview/tokenizer.json';tok=read(tokpath);enc=lambda s:encode_stream(s,tok);vocab=[bytes.fromhex(s) for s in tok['bytes']]
  inputs=[tokpath,PRE/'semantic-sample.json',PRE/'response-turns.json',R/'multiview/train.index.json',R/'multiview/train.tokens.bin',R/'sources/documents.jsonl',R/'added-human-source/documents.jsonl',R/'execution/context-auxiliary-pool.json']
  feature=read(PRE/'response-turns.json');index=read(R/'multiview/train.index.json');assert sha(inputs[4])==index['tokensSha256']==feature['trainTokensSha256'];assert sha(tokpath)==feature['tokenizerSha256'];assert sha(inputs[3])==feature['trainIndexSha256']
  tokens=np.memmap(inputs[4],dtype='<u4',mode='r');docs={}
  for p in inputs[5:7]:
   for line in p.open():
    d=json.loads(line);assert d['partition']=='train';docs[d['originalDocument']]=d
  cases=[]
  def condition(text,**meta):
   ids=enc(text);assert b''.join(vocab[t]for t in ids)==text.encode();return dict(prefixText=text,prefixTokens=[1]+ids,prefixSha256=digest(text),inputTokensWithBos=1+len(ids),**meta)
  for x in read(PRE/'semantic-sample.json')['rows']:
   if x['rankWithinSource']>6:continue
   c=dict(id=f"train-{x['source']}-{x['rankWithinSource']:02}",split='TRAIN',source=x['source'],document=x['document'],targetText=x['next']['text'],goldTokens=enc(x['next']['text']),targetOrdinal=x['next']['ordinal'],sourceSha256=x['sourceSha256'],sourceTextSha256=x['sourceTextSha256'],license=x['license'],attribution=x['attribution'],sourceUrl=x['sourceUrl'],contentSpans=[])
   c['conditions']={'correct':condition('\n'.join(u['text'] for u in x['context'])+'\n',contextOrdinals=[u['ordinal']for u in x['context']])};cases.append(c)
  for source,probe,base in [('realpersona',R47/'execution/content-native-dev/probes.json',pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/development')),('mrmp',R47/'fixed-source-mrmp-dev/probes.json',pathlib.Path('/workspace/mrmp-fresh-dev-source/development'))]:
   inputs.append(probe);pd=read(probe)
   for x in pd['probes']:
    p=base/pathlib.PurePosixPath(x['sourcePath']).name;assert sha(p)==x['sourceSha256'];us=read(p)['utterances'];j=x['utteranceEndInclusive']+1;text='\n'.join(u['text']for u in us[x['utteranceStart']:j])+'\n';assert text==x['prefix'];inputs.append(p)
    doc=('realpersona:'+p.stem) if source=='realpersona' else ('mrmp:'+p.stem)
    cases.append(dict(id=x['id'],split='exposed-DEV',source=source,document=doc,targetText=us[j]['text'],goldTokens=enc(us[j]['text']),targetOrdinal=j,targetUtteranceId=us[j]['utterance_id'],sourcePath=x['sourcePath'],sourceSha256=x['sourceSha256'],sourceCommit=pd['sourceCommit'],license='CC-BY-SA-4.0',attribution=('Sanae Yamashita et al., RealPersonaChat (PACLIC 2023)' if source=='realpersona' else 'Taro Tsuda et al. (2025), SemDial pp193–202'),conditions={'correct':condition(text,contextOrdinals=list(range(x['utteranceStart'],j)))},contentSpans=[]))
  assert len(cases)==25
  unitsById={u['id']:u for u in index['documents']}
  wanted={len(c['conditions']['correct']['prefixTokens'])-1 for c in cases};assert max(wanted)<=63
  donors={}
  for u in index['documents']:
   if u['site']!='human-chat' or u['variant']!=0:continue
   document=u['sourceDocument'];source='jmrd' if document.startswith('jmrd:')else'realpersona';seq=tokens[u['offset']:u['offset']+u['length']];spans=feature['turnsByUnit'][u['id']];assert b''.join(vocab[int(t)] for t in seq).decode('utf8')==docs[document]['text']
   for j in range(1,len(spans)):
    start=spans[max(0,j-2)][1];end=spans[j][1]
    if start is None or end is None or end-start not in wanted:continue
    ids=list(map(int,seq[start:end]));text=b''.join(vocab[t]for t in ids).decode('utf8');
    if not text.endswith('\n'):continue
    donors.setdefault((source,len(ids)),[]).append((document,j,text,u['id'],start,end))
  pool=read(R/'execution/context-auxiliary-pool.json');pooldocs={x['document']for x in pool['rows']}
  for c in cases:
   correct=c['conditions']['correct'];length=len(correct['prefixTokens'])-1;source='jmrd'if c['source']=='jmrd'else'realpersona';eligible=[]
   for d,j,text,unit,start,end in donors.get((source,length),[]):
    if d==c['document']or text==correct['prefixText']:continue
    key=digest(f"context-diagnostic-donor-v1|{c['id']}|{d}|{j}")
    exclusion=(c['id'],d,j)
    if exclusion in DONOR_EXCLUSIONS:
     audit['preOutputManualDonorExclusions'].append(dict(caseId=c['id'],document=d,followingTurnOrdinal=j,prefixText=text,prefixSha256=digest(text),rankSha256=key,reason=DONOR_EXCLUSIONS[exclusion],beforeAnyModelOutputs=True));continue
    eligible.append((key,d,j,text,unit,start,end))
   assert eligible,f"no exact donor: {c['id']}"
   eligible.sort()
   chosen=None
   for candidate in eligible:
    key,d,j,text,unit,start,end=candidate
    ids=enc(text)
    originalUnit=unitsById[unit];originalIds=list(map(int,tokens[originalUnit['offset']+start:originalUnit['offset']+end]))
    if ids!=originalIds:continue
    if enc(text+c['targetText'])!=ids+c['goldTokens']:continue
    chosen=candidate;break
   assert chosen is not None,f'no valid additive donor: {c["id"]}'
   key,d,j,text,unit,start,end=chosen;meta=docs[d]
   correct['targetConcatAdditive']=enc(correct['prefixText']+c['targetText'])==correct['prefixTokens'][1:]+c['goldTokens'];assert correct['targetConcatAdditive'],c['id']
   c['conditions']['mismatched']=condition(text,document=d,source=source,unit=unit,contextOrdinals=list(range(max(0,j-2),j)),followingTurnOrdinal=j,originalTokenStart=start,originalTokenEndExclusive=end,rankSha256=key,sourceSha256=meta['sourceSha256'],sourceTextSha256=meta['textSha256'],license=meta['license'],attribution=meta['attribution'],sourceUrl=meta['url'],targetConcatAdditive=True,semanticallyWrongGuaranteed=False)
   c['conditions']['none']=condition('',targetConcatAdditive=True);c['targetSha256']=digest(c['targetText']);c['inReferenceTrainingPool']=c['document']in pooldocs;c['donorInReferenceTrainingPool']=d in pooldocs
  checkpoint=R/'continue-10000/selected-weights.pt';aligned=R/'continue-10000/best-aligned-checkpoint.pt.chunks.json';am=read(aligned);h=hashlib.sha256()
  for part in am['chunks']:
   p=aligned.parent/part['path'];assert sha(p)==part['sha256']
   with p.open('rb')as f:
    for b in iter(lambda:f.read(1048576),b''):h.update(b)
  assert h.hexdigest()==am['sha256'];inputs.extend([checkpoint,aligned])
  auxiliary=[]
  assert len(pool['rows'])==1024 and len(pooldocs)==403
  for n,x in enumerate(pool['rows']):
   assert x['document'] in docs and x['wrongDocument'] in docs
   assert x['prefix'].rstrip('\n') in docs[x['document']]['text'] and x['target'] in docs[x['document']]['text'] and x['wrongPrefix'].rstrip('\n') in docs[x['wrongDocument']]['text']
   assert x['sourceSha256']==docs[x['document']]['sourceSha256'] and x['wrongSourceSha256']==docs[x['wrongDocument']]['sourceSha256']
   gold=enc(x['target']);assert gold==x['targetTokens']
   conditions={}
   for name,textkey,tokenskey,document,turn in [('correct','prefix','prefixTokens',x['document'],x['turn']),('mismatched','wrongPrefix','wrongPrefixTokens',x['wrongDocument'],x['wrongTurn'])]:
    text=x[textkey];assert enc(text)==x[tokenskey];assert enc(text+x['target'])==x[tokenskey]+gold
    m=docs[document];conditions[name]=condition(text,document=document,followingTurnOrdinal=turn,sourceSha256=m['sourceSha256'],sourceTextSha256=m['textSha256'],sourceUrl=m['url'],license=m['license'],attribution=m['attribution'],targetConcatAdditive=True)
   conditions['none']=condition('',targetConcatAdditive=True)
   auxiliary.append(dict(id=f'auxiliary-train-{n:04}',split='TRAIN-supervised',source='realpersona',document=x['document'],targetText=x['target'],goldTokens=gold,targetOrdinal=x['turn'],conditions=conditions,contentSpans=[],originalLexicalAnchors=x.get('anchors',[]),lexicalAnchorsAreSemanticLabels=False,freeGeneration=False))
  panel=dict(schemaVersion=1,tokenizerPath=rel(tokpath),checkpointPath=rel(checkpoint),alignedCheckpointPath=rel(aligned),expectedCheckpointSha256=sha(checkpoint),alignedSha256=am['sha256'],tokenizerSha256=sha(tokpath),prefixTokenConvention='prefixTokens includes BOS1; none=[1]; goldTokens excludes BOS/EOS',cases=cases,auxiliaryTfOnly=auxiliary,auxiliaryTfOnlyProvenance=dict(sourcePoolPath=rel(R/'execution/context-auxiliary-pool.json'),sourcePoolSha256=sha(R/'execution/context-auxiliary-pool.json'),selectionBias='Previously supervised TRAIN pool, not heldout generalization; preserve all1024 original rows and mismatches',generationAllowed=False),limitations=['12 fixed TRAIN samples are descriptive, not statistical generalization','Authentic adjacent next utterances lack universal semantic reply-to certification','Mismatched donors are different-document human TRAIN contexts, not guaranteed semantically wrong'],referencePoolUniqueDocuments=len(pooldocs),inputReceipts=[dict(path=str(p)if not p.is_relative_to(ROOT)else rel(p),sha256=sha(p))for p in inputs])
  (OUT/'panel.json').write_text(json.dumps(panel,ensure_ascii=False,indent=2)+'\n');audit.update(status='PASS',cases=len(cases),maximumCorrectNonBosTokens=max(wanted),allDonorsExactLength=True,allTargetConcatAdditive=True,panelSha256=sha(OUT/'panel.json'),builderSha256=sha(pathlib.Path(__file__)),rows=[dict(id=c['id'],correctTokens=len(c['conditions']['correct']['prefixTokens']),donorTokens=len(c['conditions']['mismatched']['prefixTokens']),goldTokens=len(c['goldTokens']),donorDocument=c['conditions']['mismatched']['document'])for c in cases])
 except Exception as e:
  audit.update(status='REFUSED');audit['failures'].append(repr(e));raise
 finally:(OUT/'panel-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
if __name__=='__main__':main()
