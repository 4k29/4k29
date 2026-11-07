"""Append only new human TRAIN units; retain every old byte and original chain/cut seeds. No model updates."""
import array,hashlib,json,pathlib,random,shutil,sys,argparse
ROOT=pathlib.Path(__file__).resolve().parent;REPO=next(p for p in ROOT.parents if (p/'.git').exists());B=REPO/'training/language';PARENT=B/'round10'
sys.path.insert(0,str(PARENT));from word_bpe import apply_rules
sys.path.insert(0,str(REPO/'training/dialogue'));from tokenizer import SPECIALS,encode_stream
sys.path.insert(0,str(B/'round11'));from prepare import segmented

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--base',type=pathlib.Path,required=True);parser.add_argument('--sources',type=pathlib.Path,required=True);parser.add_argument('--out',type=pathlib.Path,required=True);args=parser.parse_args();base=args.base;sources=args.sources;out=args.out;out.mkdir(exist_ok=False);assert sys.byteorder=='little'
 for f in ['tokenizer.json','validation.index.json','validation.tokens.bin']:shutil.copyfile(base/f,out/f)
 tok=read(out/'tokenizer.json');glyph=read(PARENT/'unicode-bpe-4681/tokenizer.json');vocab=[bytes.fromhex(x) for x in tok['bytes']];rules=tok['merges'][len(glyph['merges']):]
 ids={r['character']:r['token'] for r in read(PARENT/'character-frequencies.json')};cache={}
 def glyph_encode(text):
  result=[]
  for c in text:
   if c in ids:result.append(ids[c])
   else:
    if c not in cache:cache[c]=encode_stream(c,glyph)
    result.extend(cache[c])
  return result
 info=read(base/'train.index.json');values=array.array('I');values.frombytes((base/'train.tokens.bin').read_bytes());added=[]
 for d in [json.loads(l) for l in (sources/'documents.jsonl').read_text().splitlines()]:
  if d['partition']!='train':continue
  g=glyph_encode(d['text']);canon=apply_rules(g,rules);seed=int(hashlib.sha256(('2049|'+d['originalDocument']+'|'+str(d['startLine'])).encode()).hexdigest(),16);cuts_ids,cuts=segmented(d['text'],glyph_encode,rules,random.Random(seed))
  for variant,encoded in [(0,canon),(1,g),(2,cuts_ids)]:
   assert b''.join(vocab[t] for t in encoded)==d['text'].encode()
   uid=d['unitKey']+':view:'+str(variant);assert not any(x['id']==uid for x in info['documents']);full=[SPECIALS['bos']]+encoded+[SPECIALS['eos']];offset=len(values);values.extend(full);start=0;covered=[]
   while start<len(full)-1:
    end=min(start+257,len(full));prefix=1 if start==0 else 32
    info['rows'].append(dict(document=d['originalDocument'],unit=uid,site=d['site'],variant=variant,offset=offset+start,length=end-start,prefixLength=prefix,start=start,end=end));covered.extend(full[start+prefix:end])
    if end==len(full):break
    start=end-32
   assert covered==full[1:]
   row=dict(id=uid,sourceDocument=d['originalDocument'],site=d['site'],variant=variant,offset=offset,length=len(full),characters=len(d['text']),utf8Bytes=len(d['text'].encode()),textSha256=d['textSha256'],startLine=d['startLine'],endLine=d['endLine'],characterCuts=cuts if variant==2 else [])
   info['documents'].append(row);added.append(row)
 (out/'train.tokens.bin').write_bytes(values.tobytes());info['tokensSha256']=sha(out/'train.tokens.bin');write(out/'train.index.json',info)
 data=read(base/'data.json');data.update(newSourceManifestSha256=sha(sources/'manifest.json'),newSourceDocumentsSha256=sha(sources/'documents.jsonl'),originalPreparedDataSha256=sha(base/'data.json'),addedTrainViews=added,additionOnly=True,oldValidationUnchanged=True,reservedNewSourcesEncoded=False)
 for v in range(3):
  ds=[d for d in info['documents'] if d['variant']==v];data['stats']['train'][str(v)]=dict(units=len(ds),windows=sum(r['variant']==v for r in info['rows']),targetTokens=sum(d['length']-1 for d in ds),utf8Bytes=sum(d['utf8Bytes'] for d in ds))
 write(out/'data.json',data)
 original=read(base/'train.index.json');assert info['rows'][:len(original['rows'])]==original['rows'] and info['documents'][:len(original['documents'])]==original['documents']
 assert (out/'train.tokens.bin').read_bytes().startswith((base/'train.tokens.bin').read_bytes())
 write(out/'data-integrity.json',dict(originalTrainRowsExactlyPreserved=True,originalTrainTokenPrefixExactlyPreserved=True,validationIndexAndTokensExactlyPreserved=all(sha(out/f)==sha(base/f) for f in ['validation.index.json','validation.tokens.bin']),tokenizerExactlyPreserved=sha(out/'tokenizer.json')==sha(base/'tokenizer.json'),addedTrainUnits=read(sources/'manifest.json')['admittedUnits'],addedTrainCharacters=read(sources/'manifest.json')['admittedCharacters'],addedViews=len(added),allViewsOriginalBytesEqual=True,maskedTargetsCoveredExactlyOnce=True,reservedEncoded=False,testEncoded=False,newSourceManifestSha256=sha(sources/'manifest.json')))
 print(json.dumps(data['stats']))
