"""Build deterministic pre-output TRAIN-only correspondence assay stimuli; no model imports."""
import pathlib,json,hashlib,itertools,unicodedata,sys
ROOT=pathlib.Path(__file__).resolve().parents[4]
OUT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'training/dialogue'))
from tokenizer import encode_stream

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(s):return hashlib.sha256(s.encode()).hexdigest()
def main():
 r=ROOT/'training/language/round46';poolpath=r/'execution/context-auxiliary-pool.json';tokpath=r/'multiview/tokenizer.json';tok=json.loads(tokpath.read_text());pool=json.loads(poolpath.read_text())['rows'];docs={};receipts=[poolpath,tokpath]
 for path in [r/'sources/documents.jsonl',r/'added-human-source/documents.jsonl']:
  receipts.append(path)
  for line in path.open():
   d=json.loads(line)
   if d['site']=='human-chat':docs[d['originalDocument']]=d
 raw={};families={}
 for d in sorted({x['document']for x in pool}):
  p=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train')/(d.split(':')[1]+'.json');raw[d]=json.loads(p.read_text());assert sha(p)==docs[d]['sourceSha256'];receipts.append(p)
  families[d]=key(''.join(unicodedata.normalize('NFKC',docs[d]['text']).split()))
 groups={'fit':{},'heldaside':{}};enc=lambda s:encode_stream(s,tok)
 for i,x in enumerate(pool):
  n=len(x['prefixTokens']);d=x['document'];speakers=raw[d]['interlocutors'];sides=[int(key('assay-family-0|'+s),16)%100<58 for s in speakers]
  if len(set(sides))!=1 or n>63 or len(x['targetTokens'])>96 or len(x['target'])<8:continue
  assert enc(x['prefix'])==x['prefixTokens'] and enc(x['target'])==x['targetTokens'];assert enc(x['prefix']+x['target'])==x['prefixTokens']+x['targetTokens']
  j=x['turn'];us=raw[d]['utterances'];assert x['target']==us[j]['text'];assert x['prefix']=='\n'.join(t['text']for t in us[max(0,j-2):j])+'\n';assert us[j-1]['interlocutor_id']!=us[j]['interlocutor_id']
  group='fit'if sides[0]else'heldaside';groups[group].setdefault(n,[]).append((i,x))
 useddocs=set();usedfamilies=set();usedspeakerpairs=set();rows=[];selected=[]
 for group,count in [('fit',32),('heldaside',16)]:
  candidates=[]
  for n,items in groups[group].items():
   for (i,a),(j,b) in itertools.combinations(items,2):
    if a['document']==b['document']:continue
    if enc(a['prefix']+b['target'])!=a['prefixTokens']+b['targetTokens'] or enc(b['prefix']+a['target'])!=b['prefixTokens']+a['targetTokens']:continue
    candidates.append((key(f'assay-permutation-v1|{group}|{i}|{j}'),i,j,a,b))
  candidates.sort();chosen=0
  for rank,i,j,a,b in candidates:
   ds=[a['document'],b['document']];fs=[families[d]for d in ds];ss=[tuple(sorted(raw[d]['interlocutors']))for d in ds]
   if len(set(fs))<2 or len(set(ss))<2 or any(d in useddocs for d in ds)or any(f in usedfamilies for f in fs)or any(s in usedspeakerpairs for s in ss):continue
   chosen+=1;useddocs.update(ds);usedfamilies.update(fs);usedspeakerpairs.update(ss)
   pairids=[]
   for original,donor,idx in [(a,b,i),(b,a,j)]:
    d=original['document'];od=docs[d];ident=f'{group}-{len([q for q in rows if q["group"]==group]):03}';pairids.append(ident)
    conditions={}
    for name,z in [('correct',original),('mismatched',donor)]:conditions[name]=dict(prefixText=z['prefix'],prefixTokens=[1]+z['prefixTokens'],document=z['document'],targetConcatAdditive=True)
    rows.append(dict(id=ident,group=group,split='TRAIN-diagnostic',source='realpersona',document=d,poolOrdinal=idx,targetOrdinal=original['turn'],targetText=original['target'],goldTokens=original['targetTokens'],speakers=raw[d]['interlocutors'],speakerPairFamily=list(sorted(raw[d]['interlocutors'])),normalizedDocumentFamily=families[d],sourceSha256=od['sourceSha256'],sourceTextSha256=od['textSha256'],sourceUrl=od['url'],license=od['license'],attribution=od['attribution'],conditions=conditions))
   selected.append(dict(group=group,rowIds=pairids,rankSha256=rank,manualMismatchReview='PENDING'))
   if chosen==count:break
  assert chosen==count,(group,chosen)
 fs={s for x in rows if x['group']=='fit'for s in x['speakers']};hs={s for x in rows if x['group']=='heldaside'for s in x['speakers']};assert not fs&hs
 for g in groups:
  rs=[x for x in rows if x['group']==g];assert sorted(x['conditions']['correct']['prefixText']for x in rs)==sorted(x['conditions']['mismatched']['prefixText']for x in rs)
 panel=dict(schemaVersion=1,status='CANDIDATE_NOT_APPROVED_FOR_TRAINING',cases=rows,permutationPairs=selected,tokenizerPath=str(tokpath.relative_to(ROOT)),tokenizerSha256=sha(tokpath),prefixTokenConvention='BOS included; gold excludes EOS',sourceLimitations=['Only RealPersona TRAIN source; original1024 pool previously supervised by R46; heldaside excludes assay updates only, not pretraining','Speaker-ID partition is local RP identity control; not a proof of all latent family independence','Automatic checks cannot certify semantically wrong substitutions; independent manual review required before approval'],speakerPartitionRule='SHA256(assay-family-0|speaker) mod100 <58 fit; both speakers must agree',fitUniqueSpeakers=sorted(fs),heldasideUniqueSpeakers=sorted(hs),inputReceipts=[dict(path=str(p.relative_to(ROOT))if p.is_relative_to(ROOT)else str(p),sha256=sha(p))for p in dict.fromkeys(receipts)])
 (OUT/'candidate-panel.json').write_text(json.dumps(panel,ensure_ascii=False,indent=2)+'\n')
 audit=dict(status='CANDIDATE_MANUAL_REVIEW_REQUIRED',optimizerUpdates=0,fitRows=64,heldasideRows=32,uniqueDocuments=len(useddocs),uniqueNormalizedFamilies=len(usedfamilies),uniqueSpeakerPairFamilies=len(usedspeakerpairs),fitHeldasideSpeakerOverlap=sorted(fs&hs),permutationExactLength=True,contextMarginalsPreserved=True,panelSha256=sha(OUT/'candidate-panel.json'))
 (OUT/'candidate-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 lines=[]
 for x in rows:
  lines.extend([f'### {x["id"]} {x["document"]} speakers={x["speakers"]}',f'CORRECT: {x["conditions"]["correct"]["prefixText"]!r}',f'TARGET: {x["targetText"]}',f'PERMUTED: {x["conditions"]["mismatched"]["prefixText"]!r}',''])
 (OUT/'CANDIDATE_REVIEW.txt').write_text('\n'.join(lines))
if __name__=='__main__':main()
