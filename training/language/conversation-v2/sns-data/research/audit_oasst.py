"""Independent full-path and shared-dose audit, no model or learned external assets."""
import collections,gzip,hashlib,importlib.util,json,pathlib
H=pathlib.Path(__file__).resolve().parent;V=H.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 corpus=H.parent/'derived/oasst-conversations.jsonl.gz';mfile=H.parent/'derived/oasst-metrics.json';m=json.loads(mfile.read_text());docs=[json.loads(x)for x in gzip.open(corpus,'rt')]
 spec=importlib.util.spec_from_file_location('own_sns_oasst_audit_bpe',V/'new_tokenizer.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);t=json.loads((V/'data/tokenizer.json').read_text());e=mod.Encoder(t);vocab=[bytes.fromhex(x)for x in t['bytes']]
 unique={};speaker=collections.defaultdict(set);family=collections.defaultdict(set);comp=collections.defaultdict(set);dose=collections.Counter();tot=fit=0
 for d in docs:
  split=d['split'];family[d['conversation_family']].add(split);comp[d['component']].add(split)
  for s in d['speakers']:speaker[s].add(split)
  for i,u in enumerate(d['utterances']):
   assert u['parent_id']==(d['utterances'][i-1]['id']if i else None)
   assert u['source_role']==('prompter'if i%2==0 else'assistant')
   assert u['speaker_id']in d['speakers'];assert u['quality_flags']['synthetic_explicit_false']is True
   if u['id']in unique:assert unique[u['id']]==u
   else:
    b=e(u['text']);assert len(b)==u['body_tokens'];assert b''.join(vocab[x]for x in b)==u['text'].encode();assert hashlib.sha256(u['text'].encode()).hexdigest()==u['text_sha256'];unique[u['id']]=u
   dose[u['id']]+=1;tot+=u['body_tokens']
  assert d['utterances'][-1]['source_role']=='assistant'
  fit+=1+sum(u['body_tokens']+2for u in d['utterances'])<=257
 assert all(len(s)==1 for lookup in [speaker,family,comp]for s in lookup.values())
 assert [len(docs),len(unique),sum(u['body_tokens']for u in unique.values()),tot,fit,len(comp)]==[m[k]for k in ['maximal_branches','unique_messages_used','unique_body_tokens','serialized_body_tokens','whole_context256_fit','speaker_family_exact_connected_components']]
 assert sha(corpus)==m['derived_sha256']
 result={'passed':True,'corpusSha256':sha(corpus),'metricsSha256':sha(mfile),'completeAssistantEndingBranches':len(docs),'uniqueMessages':len(unique),'uniqueBodyTokens':sum(u['body_tokens']for u in unique.values()),'serializedBodyTokens':tot,'maximumSharedAncestorRepeat':max(dose.values()),'wholeContext256Fit':fit,'speakerFamilyComponentCrossSplit':0,'components':len(comp),'independentSourceDevAvailable':any(d['split']=='DEV'for d in docs),'knownSourceLocalWriters':len(speaker),'actualOptimizerUpdates':0,'limits':['quality/relevance and individual human authorship not established by this structural audit','one giant source component prevents internal speaker-heldout DEV','shared-prefix dose does not create independent information','semantic roles differ from RP human-participant labels']}
 (H/'independent-oasst-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
