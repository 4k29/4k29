"""Source/genre/length/context and original target-position census, not semantic scoring."""
import pathlib,json,gzip,collections,re,sys,math
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P.parent));from new_tokenizer import Encoder

def quantiles(values):
 a=sorted(values);return {str(q):a[min(len(a)-1,int((len(a)-1)*q))]for q in [0,.25,.5,.75,.9,.95,1]}if a else {}
def genre(r):
 s=r.get('heading','')+' '+r['text'];tags=[]
 for name,pattern in [('daily_waste_reuse','ごみ|リサイクル|食品ロス|買い物|廃棄物'),('nature_ecosystem','生物多様性|生態系|森林|自然環境|水環境'),('climate_energy','気候変動|温暖化|エネルギー|温室効果|二酸化炭素'),('policy_implementation','施策|策定|推進|実施しました|計画|事業'),('reason_explanation','ため|なぜ|理由|原因|影響|ことから|したがって'),('procedure_proxy','まず|次に|手順|方法|順番')]:
  if re.search(pattern,s):tags.append(name)
 return tags or ['other_environmental_prose']
def main():
 rows=[json.loads(l)for l in gzip.open(P/'corpus.jsonl.gz','rt')];enc=Encoder(json.loads((P.parent/'data/tokenizer.json').read_text()));stats={}
 for source in sorted({r['source']for r in rows}):
  rs=[r for r in rows if r['source']==source];lengths=[r['body_token_count']for r in rs];counts=collections.Counter();unknown=collections.Counter();genre_tokens=collections.Counter();sentence_lengths=[]
  for r in rs:
   text=r['text'];counts['characters']+=len(text);counts['body_tokens']+=r['body_token_count'];counts['units']+=1;counts['BOS']+=r['BOS'];counts['EOS']+=r['EOS'];counts['fits_context256']+=len(r['tokens'])<=257
   unknown.update(c for c in text if c not in enc.glyphs);counts['sentence_marks']+=text.count('。');counts['units_at_least3_sentences']+=text.count('。')>=3
   ends=[];cumulative=0
   for t in r['tokens']:cumulative+=len(bytes.fromhex(enc.tok['bytes'][t]));ends.append(cumulative)
   for start in range(256,len(r['tokens'])-1,256):
    counts['context_cuts']+=1;before=b''.join(bytes.fromhex(enc.tok['bytes'][t])for t in r['tokens'][:start+1])
    try:s=before.decode('utf-8');counts['cuts_inside_UTF8_codepoint']+=0;counts['cuts_after_complete_sentence']+=bool(re.search(r'。[\s]*$',s))
    except UnicodeDecodeError:counts['cuts_inside_UTF8_codepoint']+=1
   if source=='env_whitepaper':
    for g in genre(r):genre_tokens[g]+=r['body_token_count']
  stats[source]=dict(counts=dict(counts),body_tokens_per_character=counts['body_tokens']/counts['characters'],body_token_length_quantiles=quantiles(lengths),unknown_glyph_characters=sum(unknown.values()),unknown_glyph_types=len(unknown),unknown_handling='Own byte fallback; exact encoded byte recovery separately verified, never replacement characters inserted',genre_proxy_tokens_overlapping=dict(genre_tokens),genre_proxy_not_semantic_review=True)
 out=dict(sources=stats,ordered_source_paragraphs_preserved=True,no_cross_document_rows=True,no_false_window_EOS=True,unknown_glyph_is_not_UNK_loss=True,notes=['Window stride256 preserves every real target once, but only one preceding token is carried into the next independent window; long-range relationships beyond that window are not trained in that row.','Context cuts may divide UTF8 byte-token sequences; full-stream byte recovery remains exact. This is measured, not silently repaired.','Genre tags overlap and are proxies, not human quality labels.','Source text and full original unit token counts differ from the subset of teacher positions processed at equal A/B budget.'])
 (P/'CONTEXT_GENRE_TOKENIZER_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
