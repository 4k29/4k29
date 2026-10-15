"""Post-selection token granularity/space diagnostics, never output repair or scoring."""
import pathlib,json,hashlib,re,itertools
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
glyph=read(ROOT.parent/'round10/unicode-bpe-4681/tokenizer.json');tok=read(ROOT.parent/'round11'/'multiview/tokenizer.json');base=len(glyph['bytes']);assert tok['bytes'][:base]==glyph['bytes']
models={}
for name in ['old','new']:
 path=ROOT/'execution'/f'{name}-validation.json';g=read(path);rows=[]
 for r in g['rows']:
  tokens=r['tokens'];bytecount=sum(len(bytes.fromhex(tok['bytes'][t])) for t in tokens)
  rows.append(dict(id=r['id'],site=r['site'],generatedTokens=len(tokens),generatedCharacters=len(r['text']),generatedUtf8Bytes=bytecount,appendedWordTokens=sum(t>=base for t in tokens),maxIdenticalTokenRun=max((sum(1 for _ in group) for _,group in itertools.groupby(tokens)),default=0),maxConsecutiveFullwidthSpaces=max((len(x) for x in re.findall('　+',r['text'])),default=0),eos=r['eos'],validTokens=r['validTokens']))
 total=sum(r['generatedTokens'] for r in rows);words=sum(r['appendedWordTokens'] for r in rows);bytecount=sum(r['generatedUtf8Bytes'] for r in rows);characters=sum(r['generatedCharacters'] for r in rows)
 models[name]=dict(generationSha256=sha(path),generatedTokens=total,appendedWordTokens=words,appendedWordTokenFraction=words/total,generatedUtf8Bytes=bytecount,generatedCharacters=characters,utf8BytesPerGeneratedToken=bytecount/total,charactersPerGeneratedToken=characters/total,rows=rows)
(ROOT/'execution/generation-granularity.json').write_text(json.dumps(dict(glyphVocabulary=base,wordVocabulary=len(tok['bytes']),models=models,purpose='Post-selection diagnostics of same17 unmodified autoregressive continuations; no language judgment or causal attribution is derived automatically'),ensure_ascii=False,indent=2)+'\n')
print(json.dumps({name:{k:v for k,v in data.items() if k!='rows'} for name,data in models.items()}))
