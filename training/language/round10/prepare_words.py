"""TRAIN-only short word BPE; canonical held streams and raw-byte-equal TRAIN views."""
import array,collections,hashlib,json,pathlib,random,sys
from word_bpe import extend,apply_rules
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]/'dialogue'))
from tokenizer import SPECIALS,encode_stream

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n')
def main():
 policy=read(ROOT/'word-experiment-policy.json');base_meta=read(ROOT/'preparation.json');base_dir=ROOT/f"unicode-bpe-{base_meta['merges']}";base=read(base_dir/'tokenizer.json')
 assert policy['glyphTokenizerSha256']==sha(base_dir/'tokenizer.json') and policy['rawUnitsSha256']==sha(ROOT/'units.json') and policy['fitterSourceSha256']==sha(ROOT/'word_bpe.py') and policy['preparerSourceSha256']==sha(pathlib.Path(__file__))
 units=read(ROOT/'units.json');freq=read(ROOT/'character-frequencies.json');glyphs={r['character']:r['token'] for r in freq};cache={}
 def glyph_encode(text):
  out=[]
  for c in text:
   if c in glyphs:out.append(glyphs[c])
   else:
    if c not in cache:cache[c]=encode_stream(c,base)
    out.extend(cache[c])
  return out
 train=[glyph_encode(u['text']) for u in units if u['partition']=='train'];assert all(len(row)==len(u['text']) for row,u in zip(train,[u for u in units if u['partition']=='train'],strict=True))
 for count in policy['wordMergeCandidates']:
  directory=ROOT/f'word-bpe-{count}';assert not directory.exists(),'Vocabulary preparation is immutable; use a new experiment'
  tok=extend(train,base,merges=count,max_piece_bytes=policy['maximumPieceBytes']);assert tok['wordMerges']==count
  rules=tok['merges'][len(base['merges']):];vocab=[bytes.fromhex(b) for b in tok['bytes']]
  assert tok['merges'][:len(base['merges'])]==base['merges'] and tok['bytes'][:len(base['bytes'])]==base['bytes']
  for b in vocab[len(base['bytes']):]:assert b.decode('utf-8') and len(b)<=policy['maximumPieceBytes']
  directory.mkdir();write(directory/'tokenizer.json',tok);stats={}
  for part in ['train','validation','test']:
   selected=[u for u in units if u['partition']==part];values=array.array('I');documents=[];rows=[];view_stats={}
   for n,u in enumerate(selected):
    base_ids=glyph_encode(u['text']);canonical=apply_rules(base_ids,rules)
    if n%max(1,len(selected)//32)==0:assert canonical==encode_stream(u['text'],tok)
    views=[(0,canonical)]
    if part=='train':
     rng=random.Random(int(hashlib.sha256(('2029|'+u['document']+'|'+str(u['startLine'])).encode()).hexdigest(),16));subset=[rule for rule in rules if rng.random()>=policy['alternativeWordRuleDropRate']];views.append((1,apply_rules(base_ids,subset)))
    for variant,encoded in views:
     assert b''.join(vocab[t] for t in encoded)==u['text'].encode()
     uid=u['document']+':chain:'+str(u['startLine'])+':view:'+str(variant);full=[SPECIALS['bos']]+encoded+[SPECIALS['eos']];offset=len(values);values.extend(full);start=0;covered=[]
     while start<len(full)-1:
      end=min(start+257,len(full));prefix=1 if start==0 else 32;rows.append(dict(document=u['document'],unit=uid,site=u['site'],variant=variant,offset=offset+start,length=end-start,prefixLength=prefix,start=start,end=end));covered.extend(full[start+prefix:end])
      if end==len(full):break
      start=end-32
     assert covered==full[1:]
     documents.append(dict(id=uid,sourceDocument=u['document'],site=u['site'],variant=variant,offset=offset,length=len(full),characters=len(u['text']),utf8Bytes=len(u['text'].encode()),textSha256=u['textSha256'],startLine=u['startLine'],endLine=u['endLine']))
   if sys.byteorder!='little':values.byteswap()
   path=directory/f'{part}.tokens.bin';path.write_bytes(values.tobytes());write(directory/f'{part}.index.json',dict(rows=rows,documents=documents,tokensSha256=sha(path),unit='Unmodified original chains; canonical word BPE and TRAIN-only alternative word-rule subset. Every label and true source-unit BOS/EOS retained.'))
   for variant in sorted({d['variant'] for d in documents}):
    ds=[d for d in documents if d['variant']==variant];view_stats[str(variant)]=dict(units=len(ds),windows=sum(r['variant']==variant for r in rows),targetTokens=sum(d['length']-1 for d in ds),utf8Bytes=sum(d['utf8Bytes'] for d in ds),characters=sum(d['characters'] for d in ds))
   stats[part]=dict(views=view_stats,extraViewsOnlyTrain=part=='train');print(json.dumps(dict(wordMerges=count,partition=part,stats=stats[part])),flush=True)
  meta=dict(sourceSha256=sha(ROOT/'documents.jsonl'),splitSha256=sha(ROOT/'split.json'),rawUnitsSha256=sha(ROOT/'units.json'),tokenizerSha256=sha(directory/'tokenizer.json'),glyphTokenizerSha256=sha(base_dir/'tokenizer.json'),fitterSourceSha256=sha(ROOT/'word_bpe.py'),preparerSourceSha256=sha(pathlib.Path(__file__)),wordPolicySha256=sha(ROOT/'word-experiment-policy.json'),generationPolicySha256=sha(ROOT/'generation-policy.json'),vocabulary=len(vocab),merges=len(tok['merges']),wordMerges=count,ownTrainOnly=True,externalTokenizer=False,rawBytesPreserved=True,stats=stats)
  write(directory/'data.json',meta)
 print(json.dumps(dict(prepared=True,wordMergeCandidates=policy['wordMergeCandidates'],optimizerUpdates=0)),flush=True)
if __name__=='__main__':main()
