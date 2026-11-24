"""Fresh own TRAIN-only glyph assembly plus BPE; no inherited learned IDs/rules."""
import collections,hashlib,importlib.util,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
BYTE=module('_v2_own_byte_tokenizer',ROOT/'training/dialogue/tokenizer.py')
WORD=module('_v2_own_word_bpe',ROOT/'training/language/round10/word_bpe.py')
SPECIALS={'pad':0,'bos':1,'eos':2,'speaker_a':3,'speaker_b':4,'reserved_turn':5}

def fit(train_documents,word_merges=512,sample_character_limit=400000):
    """Complete TRAIN defines glyph inventory; SHA-first TRAIN subset defines pairs."""
    counts=collections.Counter(c for d in train_documents for u in d['utterances']for c in u['text'])
    vocabulary=[b'']*6+[bytes([i])for i in range(256)];ids={b:i for i,b in enumerate(vocabulary)if b};rules=[]
    for size in [2,3,4]:
        prefixes=collections.Counter()
        for c,n in counts.items():
            raw=c.encode('utf8')
            if len(raw)>=size:prefixes[raw[:size]]+=n
        for raw,n in sorted(prefixes.items(),key=lambda kv:(-kv[1],kv[0])):
            if raw in ids:continue
            left=ids[raw[:-1]];right=ids[raw[-1:]];token=len(vocabulary)
            vocabulary.append(raw);ids[raw]=token;rules.append([left,right,token])
    glyphs={c:ids[c.encode()]for c in counts}
    parent={'schemaVersion':1,'specials':SPECIALS,'bytes':[x.hex()for x in vocabulary],
        'merges':rules,'maxPieceBytes':4,'unicodeCharacterAssembly':True,'glyphTokenIds':glyphs,
        'glyphRules':len(rules),'note':'Fresh byte inventory+Unicode assembly from v2 TRAIN only; no old learned vocabulary or rules.'}
    sample=[];selected=[];total=0
    for d in sorted(train_documents,key=lambda d:hashlib.sha256(('v2-bpe-sample-v1|'+d['id']).encode()).hexdigest()):
        chars=sum(len(u['text'])for u in d['utterances'])
        if total+chars>sample_character_limit:break
        sample.extend([[glyphs[c]for c in u['text']]for u in d['utterances']]);selected.append(d['id']);total+=chars
    assert 250000<=total<=sample_character_limit
    tok=WORD.extend(sample,parent,merges=word_merges,max_piece_bytes=18)
    tok['note']='Fresh own v2 TRAIN-only byte/glyph/BPE. Existing numerical BPE algorithm reused; no learned parent tokenizer or outside vocabulary.'
    tok['trainingCharacterTypes']=len(counts);tok['trainingCharacters']=sum(counts.values())
    tok['fitSubset']={'rule':'SHA256(v2-bpe-sample-v1|document ID) ascending complete documents until400000chars',
        'documents':selected,'characters':total,'allTrainingGlyphInventory':True}
    return tok

class Encoder:
    def __init__(self,tok):
        self.tok=tok;self.glyphs=tok['glyphTokenIds'];self.glyph=dict(tok,merges=tok['merges'][:tok['glyphRules']])
        self.word=tok['merges'][tok['glyphRules']:];self.cache={}
    def __call__(self,text):
        values=[]
        for c in text:
            if c in self.glyphs:values.append(self.glyphs[c])
            else:
                if c not in self.cache:self.cache[c]=BYTE.encode_stream(c,self.glyph)
                values.extend(self.cache[c])
        return WORD.apply_rules(values,self.word)
    def reference(self,text):return BYTE.encode_stream(text,self.tok)
