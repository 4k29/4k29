"""Independent structural/count audit; no model imported or weights opened."""
import gzip, hashlib, importlib.util, json, pathlib, collections
HERE=pathlib.Path(__file__).resolve().parent
V2=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 corpus=HERE.parent/'derived/conversations.jsonl.gz';metrics=HERE.parent/'derived/metrics.json'
 rows=[json.loads(x)for x in gzip.open(corpus,'rt')];published=json.loads(metrics.read_text())
 spec=importlib.util.spec_from_file_location('independent_sns_own_bpe',V2/'new_tokenizer.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 tokenizer=V2/'data/tokenizer.json';tok=json.loads(tokenizer.read_text());enc=mod.Encoder(tok);vocab=[bytes.fromhex(x)for x in tok['bytes']]
 speakers=collections.defaultdict(set);families=collections.defaultdict(set);components=collections.defaultdict(set)
 utterances=body=chars=pairfit=pairs=wholefit=0;rolecounts=collections.Counter();splits=collections.Counter();lengths=[]
 for d in rows:
  s=d['split'];splits[s]+=1;families[d['conversation_family']].add(s);components[d['component']].add(s);rolecounts[len(d['speakers'])]+=1
  for person in d['speakers']:speakers[person].add(s)
  ids=set();sizes=[]
  for i,u in enumerate(d['utterances']):
   assert u['id'] not in ids;ids.add(u['id']);assert u['speaker_id']in d['speakers'];assert u['parent_id']is None
   assert u['previous_in_order_id']==(d['utterances'][i-1]['id']if i else None)
   assert set(u['mention_to'])<=set(d['speakers'])
   value=enc(u['text']);assert len(value)==u['body_tokens'];assert b''.join(vocab[x]for x in value)==u['text'].encode()
   assert hashlib.sha256(u['text'].encode()).hexdigest()==u['text_sha256'];sizes.append(len(value));lengths.append(len(value))
   utterances+=1;body+=len(value);chars+=len(u['text'])
  pairs+=max(0,len(sizes)-1);pairfit+=sum(1+sizes[i-1]+sizes[i]+4<=257 for i in range(1,len(sizes)))
  wholefit+=1+sum(x+2 for x in sizes)<=257
 assert all(len(x)==1 for lookup in [speakers,families,components]for x in lookup.values())
 assert [len(rows),utterances,body,chars,pairs,pairfit,wholefit]==[published[k]for k in ['dialogues','utterances','body_tokens','characters','adjacent_pairs','adjacent_pair_context256_fit','whole_context256_fit']]
 assert len(speakers)==published['distinct_source_local_speakers'];assert dict(splits)==published['split_documents'];assert sha(corpus)==published['derived_sha256']
 lengths.sort()
 result={'passed':True,'scope':'independent full derived-structure and own-BPE re-encoding; not semantic quality, consent or human rater proof','corpusSha256':sha(corpus),'metricsSha256':sha(metrics),'tokenizerSha256':sha(tokenizer),'dialogues':len(rows),'utterances':utterances,'bodyTokens':body,'characters':chars,'speakerCountsPerConversation':dict(rolecounts),'distinctSourceLocalSpeakers':len(speakers),'speakerFamilyComponentCrossSplit':0,'speakerConnectedComponents':len(components),'componentDialogueCounts':dict(collections.Counter(d['component']for d in rows)),'splitDocuments':dict(splits),'wholeConversationContext256Fit':wholefit,'chronologicalAdjacentPairs':pairs,'adjacentPairContext256Fit':pairfit,'explicitReplyParents':0,'utteranceTokenQuantiles':{str(q):lengths[min(len(lengths)-1,int(q*(len(lengths)-1)))]for q in [.5,.9,.99]},'modelCalls':0,'optimizerUpdates':0,'sealedTestRead':False,'actualTwoRoleCompatibility':sum(n for k,n in rolecounts.items()if k<=2),'limitations':['last previous_in_order is not a semantic reply edge','source-local identifiers do not prove cross-source author independence','sampled near-duplicate retrieval is not exhaustive','current two-role adapter cannot preserve a three-person dialogue']}
 (HERE/'independent-corpus-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
