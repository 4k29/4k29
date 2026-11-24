"""Audit reviewed source sentence ranges against archived TRAIN tokens and family names."""
import gzip
import hashlib
import json
import sys
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path
from study import BASE,ROOT,read,save

sys.path.insert(0,str(BASE))
from new_tokenizer import Encoder

# (first sentence, short-history sentence, common target sentence, exclusive end)
WIKI={
 '小鹿田焼':(0,2,3,5,'短い履歴にも小鹿田焼と窯元があり、陶芸技法の指定から地元の施設へ進む。'),
 '欄間':(3,4,5,6,'短い履歴に建具の名称と用途上の特徴があり、歴史の説明がつながる。'),
 '水引':(0,1,2,3,'水引の用途を残し、素材と発達に接続する。'),
 '漆器':(3,4,5,7,'漆器の工程が短い履歴にあり、「この工程」の参照と素地の説明を保つ。'),
 '組子細工':(2,3,4,6,'技法の名前と作り方を残し、模様・用途・産地を続ける。'),
 '行灯':(0,2,3,4,'行灯と携行用途の由来を残し、携行用から据付型への変遷につなぐ。'),
 '畳':(0,1,2,4,'畳表・畳縁の定義が短い履歴にあり、素材と縁なしの説明が成立する。'),
 'けん玉':(6,7,8,9,'名前と日月ボールの関係を残し、同じ日月ボールに由来する記念日へ進む。'),
 '折り紙':(3,4,5,7,'折り紙とORIGAMIの文化的広がりを残し、創作と研究の説明が続く。'),
 '粉茶':(5,6,7,9,'粉茶は茶葉で茶殻が残るという対比の前提が短い履歴にある。'),
 'うちわ':(3,4,5,7,'穴開きうちわの例から、絵柄と団扇の産地へつながる。'),
 '硯':(1,2,3,5,'硯箱と硯を明示する文から、産地と職人の説明へつながる。'),
 '紙芝居':(0,2,3,4,'短文に立絵と平絵の区別があり、平絵を主題とする後続が成立する。'),
 'すり鉢':(3,5,6,7,'すり鉢を臼とする文から、同じ器具の原型と溝の起源へ続く。'),
 '麺棒':(4,5,6,7,'麺棒の形状を明示し、それを用いる台の説明へ接続する。'),
 '茶碗':(1,2,3,4,'飯茶碗を明示する文が残り、呼称の区別という逆接が成立する。'),
}
PART2={'盆栽':(0,0,1,3,'盆栽の定義から育て方と呼称へ続く。'),
 '定規':(0,0,1,3,'道具の定義から用途と素材へ続く。'),
 '湯たんぽ':(0,0,1,3,'道具の定義から素材と用途へ続く。'),
 '落款':(0,0,1,4,'落款の定義から款記と落款印の説明へ続く。')}
LEGACY={
 '早川のビランジュ':(0,2,3,5,'樹幹の特徴を残し、同じ樹木の調査と若い幹の説明へ続く。'),
 '箱根火山の形成史':(0,1,2,3,'浅い基盤岩の観測事実が残り、陥没説との矛盾へ続く。'),
 'ローマ建築':(0,2,3,4,'地域差を明示する文を保ち、ただし以下の東西差の説明へ進む。'),
}
ARCHIVES=['modern-corpus/next-foundation/corpus.jsonl.gz','mixed-retention-study/corpus.json.gz',
 'mixed-volume-study/corpus.json.gz','foundation-absorption-study/corpus.jsonl.gz',
 'diverse-foundation/corpus.jsonl.gz','pretraining-scale/corpus.jsonl.gz',
 'broad-prose-replay/TRAIN.json','prose-budget-scale/TRAIN.json']

def normalize(s):
    return ''.join(unicodedata.normalize('NFKC',s.split('|')[-1]).split()).casefold()

def blob(path):
    repo=ROOT.parents[3]
    return subprocess.check_output(['git','show',f'HEAD:{(BASE/path).relative_to(repo)}'],cwd=repo)

def digest(x):
    return hashlib.sha256(x).hexdigest()

def ngrams(t):
    return zip(*(t[i:] for i in range(12)))

def main():
    tok=read(BASE/'data/tokenizer.json')
    enc=Encoder(tok); pieces=list(map(bytes.fromhex,tok['bytes']))
    raw=[]
    for page in read(ROOT/'SOURCE_SNAPSHOTS.json'):
        title=page['title']
        if title not in WIKI and title not in PART2:continue
        rev=page['revisions'][0]['revid']
        raw.append((title,page['extract'],(WIKI|PART2)[title],dict(origin='Wikimedia extracts and revisions',revision=rev,
                  url=f'https://ja.wikipedia.org/w/index.php?oldid={rev}',
                  attribution=f'https://ja.wikipedia.org/w/index.php?title={title}&action=history',
                  license='CC BY-SA 4.0',rights_url='https://ja.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=rightsinfo&format=json')))
    historic=blob('foundation-stage/prose-dev.json')
    for r in json.loads(historic)['cases'][::2]:
        if r['title'] in LEGACY:
            raw.append((r['title'],r['prefix_text']+r['source_remainder'],LEGACY[r['title']],
                        dict(origin='Archived exploratory DEV',source_sha=digest(historic),source_id=r['id'],
                             attribution=f"https://ja.wikipedia.org/w/index.php?title={r['title']}&action=history",
                             license='CC BY-SA 3.0 per inherited JaQuAD corpus; original revision unresolved')))
    rows=[]; excluded=[]
    for title,t,(a,b,c,d,reason),meta in raw:
        sentences=[s+'。' for s in t.split('。')[:-1]]
        if d>len(sentences):
            excluded.append([title,'missing_sentence']);continue
        parts=[''.join(sentences[a:b]),''.join(sentences[b:c]),''.join(sentences[c:d])]
        ids=[enc(x) for x in parts]
        text=''.join(parts)
        seq=sum(ids,[])
        if len(seq)>256 or enc(text)!=seq or enc(''.join(parts[1:]))!=ids[1]+ids[2] or b''.join(pieces[x] for x in seq).decode()!=text:
            excluded.append([title,'context_or_byte_BPE_boundary']);continue
        rows.append(dict(id=title,family=normalize(title),text=text,source_excerpt_sha256=digest(t.encode()),
            text_sha256=digest(text.encode()),cut=len(ids[0]),full=ids[0]+ids[1],short=ids[1],gold=ids[2],
            maxNewTokens=min(64,257-len(ids[0]+ids[1])),provenance=meta,review=reason,exposure=[]))
    held=defaultdict(set)
    for i,r in enumerate(rows):
        for ng in ngrams(r['full']+r['gold']):held[ng].add(i)
    archive_sha={}
    for name in ARCHIVES:
        data=blob(name)
        archive_sha[name]=digest(data)
        value=gzip.decompress(data) if name.endswith('.gz') else data
        records=(map(json.loads,value.splitlines()) if '.jsonl' in name else json.loads(value))
        for r in records:
            if r.get('split','train') not in ('train',None):continue
            fam={normalize(str(r.get(k,''))) for k in ('family','title','component')}
            seq=r.get('tokens',[]) or r.get('prefix',[])+r.get('gold',[])
            hits=set()
            for ng in ngrams(seq):
                hits.update(held.get(ng,()))
            for i,item in enumerate(rows):
                match='family' if item['family'] in fam else '12token' if i in hits else None
                if match and not any(p[0]==name and p[1]==match for p in item['exposure']):
                    item['exposure'].append([name,match,r.get('id')])
    for r in rows:
        r['group']='known_train_match' if r['exposure'] else 'old_dev' if r['provenance']['origin']=='Archived exploratory DEV' else 'no_known_train_match'
    save(ROOT/'DEV_PART2.json',dict(cases=[r for r in rows if r['id'] in PART2],excluded=[r for r in excluded if r[0] in PART2],archive_sha=archive_sha))
    save(ROOT/'DEV.json',dict(cases=[r for r in rows if r['id'] not in PART2],excluded=[r for r in excluded if r[0] not in PART2],archive_sha=archive_sha,
          limit='No exhaustive source-history or semantic paraphrase check. Archived title and exact 12-token matching in the listed TRAIN corpora. Human review single evaluator.'))
    print([(x['id'],x['group'],len(x['full']),len(x['gold'])) for x in rows],excluded)

if __name__=='__main__':
    main()
