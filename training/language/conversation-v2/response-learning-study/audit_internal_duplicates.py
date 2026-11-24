"""Additional-vs-existing and additional-vs-additional duplicate audit; no model calls."""
import pathlib,json,collections,difflib,unicodedata,os,base64,gzip
P=pathlib.Path(__file__).resolve().parent;V=pathlib.Path(os.environ.get('CE_V2_ROOT',str(P.parent)));O=pathlib.Path(os.environ.get('CE_PRIOR_ROOT',str(V/'response-ce-study')))
b=gzip.decompress(base64.b64decode((O/'CANDIDATE_SPANS.json.gz.b64').read_text()));old=json.loads(b)['parts']['train'];new=json.loads((P/'ADDITIONAL_DATA.json').read_text())['parts']['train'];tok=json.loads((V/'data/tokenizer.json').read_text());bs=[bytes.fromhex(t)for t in tok['bytes']]
decode=lambda r:b''.join(bs[t]for t in r['tokens'][r['response_body_start']:-1]).decode();canon=lambda s:''.join(unicodedata.normalize('NFKC',s).split()).casefold();groups=collections.defaultdict(list)
for r in old+new:groups[canon(decode(r))].append(r['id'])
exact=[v for v in groups.values()if len(v)>1];near=[]
for i,r in enumerate(new):
 for q in old+new[:i]:
  ratio=difflib.SequenceMatcher(None,canon(decode(r)),canon(decode(q)),autojunk=False).ratio()
  if ratio>=.8:near.append(dict(first=q['id'],additional=r['id'],ratio=ratio))
assert not exact and not near
(P/'INTERNAL_DUPLICATES.json').write_text(json.dumps(dict(exact_normalized_response_groups=exact,near_pairs_involving_additional=near,method='NFKC whitespace removal casefold; SequenceMatcher threshold0.8; source-family review separate',body_token_count_not_increased_by_repetition=True),ensure_ascii=False,indent=2)+'\n')
