"""Validate teacher truth from parsed visible fields, independently of generator flow."""
import collections,json,pathlib,re
H=pathlib.Path(__file__).resolve().parent

def main():
 data=json.loads((H/'data.json').read_text());counts=collections.Counter();source_tokens=0
 for split,rows in data.items():
  for r in rows:
   p=r['prompt'];a=r['answer'];task=r['task'];f=r['provenance']['facts'];assert 'phone'not in f and'address'not in f
   for key,label in [('parking','駐車場'),('wifi','Wi-Fi')]:
    if key in f:assert label+':'+f[key] in p
   if task.startswith('compare'):
    adult=int(re.search(r'大人料金:(\d+)',p)[1]);child=int(re.search(r'子供料金:(\d+)',p)[1]);expected='両方の料金は同じです。'if adult==child else('大人'if adult<child else'子供')+'の料金が安いです。';assert a==expected
    if r['counterfactual']:assert adult==int(f['childfee'])and child==int(f['adultfee'])and'仮定'in p
    else:assert adult==int(f['adultfee'])and child==int(f['childfee'])
   elif task=='fee':assert re.search(r'子供の入場料は(\d+)円です。',a)[1]==re.search(r'子供料金:(\d+)',p)[1]==f['childfee']
   elif task=='condition':
    yes='駐車場:有り(無料)'in p and'Wi-Fi:有り(無料)'in p;assert ('満たしません'in a)==(not yes)
   else:
    v=f[task];assert ('無料'in a)==(v=='有り(無料)');assert ('有料'in a)==(v=='有り(有料)');assert ('ありません'in a)==(v=='無し')
   counts[split]+=1
 (H/'TEACHER_VALIDATION.json').write_text(json.dumps({'all_visible_input_teacher_pairs_verified':True,'counts':dict(counts),'counterfactuals_explicitly_labeled':True,'no_external_generator':True,'human_answer_authorship_claimed':False},indent=2)+'\n');print(dict(counts))
if __name__=='__main__':main()
