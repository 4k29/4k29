"""Exact source/family/speaker and adjacent-pair overlap; not semantic equivalence certification."""
import json,pathlib,hashlib,unicodedata,collections,os
__import__('os').umask(0o077)
P=pathlib.Path(__file__).resolve().parent;V=pathlib.Path(os.environ.get('CE_V2_ROOT','/workspace/4k29/training/language/conversation-v2'))
def main():
 norm=lambda s:''.join(unicodedata.normalize('NFKC',s).split())
 train=[json.loads(l)for l in (V/'data/train.docs.jsonl').open()];dev=[json.loads(l)for l in (V/'data/dev.docs.jsonl').open()];qmap=collections.defaultdict(set);pairmap=collections.defaultdict(set)
 for d in train:
  for a,b in zip(d['utterances'],d['utterances'][1:]):qmap[norm(a['text'])].add(d['id']);pairmap[norm(a['text']),norm(b['text'])].add(d['id'])
 cards=json.loads((P/'LOCAL_REVIEW_CARDS.json').read_text());review=json.loads((P/'REVIEW.json').read_text())['cases'];approved={r['id']for r in review if r['partition']=='dev'and r['decision']=='conditional_candidate'};rows=[]
 for r in cards['dev']:
  if r['id']not in approved:continue
  q=norm(r['history_text'][-1]);a=norm(r['response_text']);rows.append(dict(id=r['id'],same_normalized_last_utterance_train_documents=len(qmap.get(q,[])),same_normalized_pair_train_documents=len(pairmap.get((q,a),[]))))
 x=dict(train_dev_sourceTextSHA_overlap=len({d['sourceTextSha256']for d in train}&{d['sourceTextSha256']for d in dev}),known_pair_overlap=sum(r['same_normalized_pair_train_documents']>0 for r in rows),last_utterance_overlap=sum(r['same_normalized_last_utterance_train_documents']>0 for r in rows),rows=rows,full_semantic_family_independence_established=False,scope='Exact canonical whole-source/speaker/family audit plus canonical adjacent pairs; shared generic intents are not proof of semantic family independence.',optimizer_calls=0,model_forwards=0)
 (P/'LEAKAGE_AUDIT.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
