"""Supplemental post-primary context intervention; never a sealed TEST."""
import copy,hashlib,json,pathlib,sys,importlib.util
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))
import torch
from checkpoint_io import load as load_snapshot
from core import restore
from eval_core import greedy
from new_tokenizer import Encoder

def main():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);data=json.loads((H/'data.json').read_text());plan=json.loads((H/'PLAN.json').read_text());seen={r['entity']for r in data['dev']if r['id']in plan['evaluation']['dev_ids']};by={r['entity']:r for r in data['dev']if r['entity']not in seen};names=sorted(by,key=lambda x:hashlib.sha256(x.encode()).hexdigest())[:3];tok=json.loads((V/'data/tokenizer.json').read_text());enc=Encoder(tok);pieces=[bytes.fromhex(x)for x in tok['bytes']];cases=[]
 for name in names:
  for slot,label in [('parking','駐車場'),('wifi','Wi-Fi')]:
   for free in [True,False]:
    f={'parking':'無し','wifi':'無し'};f[slot]='有り(無料)'if free else'無し';p='仮定の設備資料\n施設:'+name+'、駐車場:'+f['parking']+'、Wi-Fi:'+f['wifi']+'\n質問：資料の'+label+'は使えますか。料金についても教えてください。';cases.append({'entity':name,'slot':slot,'free':free,'prompt':p,'prefix':[1,3]+enc(p)+[2,4]})
 (H/'CONTEXT_PROBE_PLAN.json').write_text(json.dumps({'scope':'post-primary supplemental programmatic diagnostic, not independent human evaluation','cases':cases,'single_changed_field_within_pair':True,'models':['full512','response512','full-extra','response-extra'],'automatic_conservative_pair_criterion':'each output correct value, no wrong subject, both counterfactual sides correct; full reading remains needed'},ensure_ascii=False,indent=2)+'\n');settings=json.loads((V/'PLAN.json').read_text())['training'];summary={}
 for name in ['full512','response512','full-extra','response-extra']:
  fn=name.replace('512','-512');st=load_snapshot(fn)['trajectory'];model,opt,rng=restore(copy.deepcopy(st),settings);model.eval();rows=[]
  with torch.no_grad():
   for c in cases:
    g=greedy(model,c['prefix'],pieces,max_new=48);text=g['text'];wrong='Wi-Fi'if c['slot']=='parking'else'駐車場';valid=(('無料'in text and not any(s in text for s in ['ない','ありません','有料']))if c['free']else'ありません'in text)and wrong not in text;rows.append({**c,**g,'conservative_value_candidate':valid})
  pairs=sum(rows[i]['conservative_value_candidate']and rows[i+1]['conservative_value_candidate']for i in range(0,len(rows),2));(H/'evaluation-extra'/(name+'-context.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');summary[name]={'paired_value_candidates':pairs,'pairs':len(rows)//2,'not_formal_human_pass':True}
 (H/'evaluation-extra/context-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
if __name__=='__main__':main()
