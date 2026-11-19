"""Apply reviewed overrides and reproduce individual scoring records."""
import gzip
import json
import re
from prepare import ROOT,BASE,read,save

def first_conspicuous_cycle(tokens):
    for j in range(len(tokens)):
        for n in range(1,min(16,(len(tokens)-j)//3)+1):
            if tokens[j:j+n]==tokens[j+n:j+2*n]==tokens[j+2*n:j+3*n]:
                return j
    return None

def review():
    plan=read(ROOT/'PLAN.json')
    notes=read(ROOT/'REVIEW_NOTES.json')
    labels={r['id']:r for r in read(BASE/'gv-prose-pilot/SEMANTIC_REVIEW.json')['cases']['initial']}
    base={r['id']:r for r in json.load(gzip.open(ROOT/'A-0.json.gz'))['cases'] if r['panel']=='caption'}
    output={}
    for arm in plan['arms']:
        for step in plan['steps']:
            key=f'{arm}-{step}'
            rules=notes[key]
            checked=[]
            for i,r in enumerate(json.load(gzip.open(ROOT/f'{key}.json.gz'))['cases']):
                panel=r['panel'];gen=r['generated'];s=r['text']
                exact=bool(r['gold']) and gen==r['gold']
                same=panel=='caption' and gen==base[r['id']]['generated']
                caption=panel=='caption' and (i in rules['caption'] or same and labels[r['id']]['decision']=='natural_short_text_only')
                two=panel!='caption' and (panel=='train' and exact or i in rules['two'])
                ending=caption and (i in rules.get('ending',[]) or same and labels[r['id']].get('ending_only_or_supplied_noun_completion',False))
                cycle=None if two or caption else first_conspicuous_cycle(gen)
                reason=('学習元の続きと全tokenが一致' if panel=='train' and exact else
                        '初期の保存済み判定と生成が同一' if same else
                        '入力に対して自然な短文として成立' if caption else
                        '参照と異なるが同じ話題を二文で展開' if two else
                        '自律部分の内容または文の接続が評価基準を満たさない')
                checked.append(dict(id=r['id'],caption=caption,two=two,ending_only=ending,harm=cycle is not None,
                                    triple_cycle_witness=cycle,reason=reason,leakage=rules.get('leakage',{}).get(str(i))))
            output[key]=checked
    save(ROOT/'JUDGMENTS.json',output)

if __name__=='__main__':
    review()
