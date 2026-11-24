"""Aggregate actual source text/token/context data, without presenting proxy tags as semantics."""
import collections,statistics
from common import *
rows=[r for r in gzrows(D/'corpus.jsonl.gz')if r['split']=='train'];tok=read(V/'data/tokenizer.json');pieces=[bytes.fromhex(s)for s in tok['bytes']];out={};windows=json.load(gzip.open(D/'schedule.json.gz','rt'))['batches'];badstart=badend=0;turn=collections.Counter();chars=collections.Counter()
for source in sorted({r['source']for r in rows}):
 group=[r for r in rows if r['source']==source];texts=[''.join(u['text']for u in r['utterances'])if r['kind']=='human_dialogue'else r['text']for r in group];counts=collections.Counter(c for s in texts for c in s);chars.update(counts);n=sum(len(r['body_tokens'])for r in group);lengths=sorted(len(r['tokens'])for r in group)
 out[source]=dict(units=len(group),characters=sum(counts.values()),body_tokens=n,tokens_per_character=n/sum(counts.values()),body_share=n/sum(len(r['body_tokens'])for r in rows),unknown_glyph_occurrences=sum(v for c,v in counts.items()if c not in tok['glyphTokenIds']),unknown_glyph_types=sum(c not in tok['glyphTokenIds']for c in counts),max_unit_tokens=max(lengths),units_over256=sum(x>257 for x in lengths),whole_units_fit256=sum(x<=257 for x in lengths)/len(lengths),BOS_units=sum(r['BOS']for r in group),EOS_units=sum(r['EOS']for r in group))
for b in windows:
 for w in b:
  ts=w['tokens'];raw=b''.join(pieces[t]for t in ts if t>=6)
  try:raw.decode('utf8','strict')
  except UnicodeDecodeError as e:
   badstart+=e.start==0;badend+=e.end==len(raw)
for r in rows:
 if r['kind']=='human_dialogue':
  for u in r['utterances']:
   s=u['text'];turn['total']+=1;turn['contains_question_mark_proxy']+=('?'in s or'？'in s);turn['multiple_sentence_ending_proxy']+=sum(s.count(x)for x in ['。','！','？','!','?'])>=2
write(D/'TOKEN_CONTEXT_AUDIT.json',dict(sources=out,window_count=sum(len(b)for b in windows),UTF8_partial_start_windows=badstart,UTF8_partial_end_windows=badend,partial_window_note='Full original units roundtrip exactly. A context cut can fall between fallback byte tokens; these counts describe incomplete context bytes, not repaired/replaced source or arbitrary EOS.',human_turn_proxies=dict(turn),proxy_is_not_content_success=True,genre='source-based prose/encyclopedia/education/travel/human everyday dialogue; no exhaustive semantic topic labeling',body_token_count='independent retained original positions after document dedup; naturally repeated phrases across independently authored turns remain, unique utterance-string tokens reported separately in CORPUS_AUDIT',speaker_source_linkage='RP source IDs only; no cross-service identity matching'))
print(out)
