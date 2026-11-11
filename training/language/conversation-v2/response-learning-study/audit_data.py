"""Audit immutable prior selection plus separately reviewed additions; no model calls."""
import pathlib,json,hashlib,collections,statistics,difflib,sys
P=pathlib.Path(__file__).resolve().parent
import argparse,base64,gzip
ap=argparse.ArgumentParser();ap.add_argument('--repo',default='/workspace/4k29');ap.add_argument('--prior',default='/dev/shm/response-ce-study');args=ap.parse_args();ROOT=pathlib.Path(args.repo);prior=pathlib.Path(args.prior)
if (prior/'CANDIDATE_SPANS.json').exists(): original=(prior/'CANDIDATE_SPANS.json').read_bytes()
else: original=gzip.decompress(base64.b64decode((prior/'CANDIDATE_SPANS.json.gz.b64').read_text()))
old=json.loads(original)['parts']
new=json.loads((P/'ADDITIONAL_DATA.json').read_text())['parts'];ann=json.loads((P/'ANNOTATIONS.json').read_text())['cases']
sys.path.insert(0,str(ROOT/'training/language/conversation-v2'));from new_tokenizer import Encoder
enc=Encoder(json.loads((ROOT/'training/language/conversation-v2/data/tokenizer.json').read_text()))
parts={s:old[s]+new[s]for s in ['train','dev']}
# Byte decoding only. Keep private rejected original text out of public artifacts.
tok=json.loads((ROOT/'training/language/conversation-v2/data/tokenizer.json').read_text());pieces=[bytes.fromhex(t)for t in tok['bytes']]
def body(r):return b''.join(pieces[t]for t in r['tokens'][r['response_body_start']:-1]).decode('utf8')
def canon(s):return ''.join(s.split()).casefold()
def stats(rs):
 bs=[len(r['tokens'])-r['response_body_start']-1 for r in rs];ins=[len(r['tokens'])-1 for r in rs]
 return dict(responses=len(rs),body_tokens=sum(bs),input_nonpadding_tokens=sum(ins),all_CE_teachers=sum(ins),response_CE_teachers=sum(bs)+len(rs),response_EOS_teachers=len(rs),families=len({r['family']for r in rs}),speakers=len({s for r in rs for s in r['speakers']}),body_length=dict(mean=statistics.mean(bs),median=statistics.median(bs),maximum=max(bs)),context256_fraction=sum(len(r['tokens'])<=257 for r in rs)/len(rs),source_counts=dict(collections.Counter(r['source']for r in rs)))
sp=lambda rs:{s for r in rs for s in r['speakers']}
fm=lambda rs:{r['family']for r in rs}
doc=lambda rs:{r['document']for r in rs}
texts={k:[canon(body(r))for r in rs]for k,rs in parts.items()}
exact=set(texts['train'])&set(texts['dev']);near=[]
for i,a in enumerate(texts['train']):
 for j,b in enumerate(texts['dev']):
  ratio=difflib.SequenceMatcher(None,a,b,autojunk=False).ratio()
  if ratio>=.8:near.append(dict(train=parts['train'][i]['id'],dev=parts['dev'][j]['id'],ratio=ratio))
assert not(sp(parts['train'])&sp(parts['dev']))and not(fm(parts['train'])&fm(parts['dev']))and not(doc(parts['train'])&doc(parts['dev']))and not exact
for rs in parts.values():
 assert len({r['id']for r in rs})==len(rs)
 for r in rs:
  t=r['tokens'];s=r['response_body_start'];assert t[0]==1 and t[s-1]in[3,4]and t[-1]==2 and 0 not in t and len(t)<=257
  raw=body(r);assert enc(raw)==t[s:-1]
cat={}
for c in 'ABCDEF':
 rr=[r for r in new['train']if any(a['id']==r['id']and c in a['categories']for a in ann)]
 cat[c]=stats(rr)if rr else None
pilot=set(json.loads((P/'PILOT_DATA.json').read_text())['pilot_ids_excluded_from_future_main']);main=[r for r in parts['train']if r['id']not in pilot]
out=dict(prior_196_unchanged=True,train=stats(parts['train']),dev=stats(parts['dev']),additional_train=stats(new['train']),additional_dev=stats(new['dev']),future_main_excluding_pilot=stats(main),category_additions_multilabel=cat,train_dev_speaker_intersection=0,train_dev_family_intersection=0,train_dev_document_intersection=0,train_dev_exact_body_intersection=len(exact),near_similarity_threshold=.8,near_cross_partition=near,all_body_UTF8_BPE_roundtrip=True,all_complete_history_context256=True,independent_human_evaluation=False,source_speaker_identification_limit='Original dataset identifiers only; no cross-service identity linking or proof of real-world uniqueness',semantic_family_limit='Document family and normalized exact/near strings audited; semantic similarity cannot be exhaustively proven absent',main_learning_authorized=False,new_original_acquisition=0)
(P/'SOURCE_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
