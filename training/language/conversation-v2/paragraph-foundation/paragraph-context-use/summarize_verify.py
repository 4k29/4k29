"""Post-run verification and tables; never loads a model or changes frozen inputs."""
import gzip, hashlib, json, statistics
from collections import Counter
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
ROOT=P.parents[4]
def read(n): return json.loads((P/n).read_text())
def sha(b): return hashlib.sha256(b).hexdigest()
r=read('RESULTS.json'); a=read('AUXILIARY_RESULTS.json'); e=read('EXECUTION.json')
f=read('FREEZE.json')
for name,digest in f['sha256'].items(): assert sha((ROOT/name).read_bytes())==digest,name
max_error=0.
for result,aux in [(r,False),(a,True)]:
 meta=result['raw_logits']; packed=(P/meta['file']).read_bytes(); raw=gzip.decompress(packed)
 assert sha(packed)==meta['gzip_sha256'] and sha(raw)==meta['raw_sha256']
 x=np.frombuffer(raw,dtype='<f4').reshape(meta['shape']).astype(np.float64)
 rows=[]
 for case in result['cases']:
  for k in ['C','U']:
   rows.extend(case['conditions'][k] if aux else [case[k]])
 assert len(rows)==len(x)
 for v,out in zip(x,rows):
  lp=v-(np.max(v)+np.log(np.exp(v-np.max(v)).sum())); prob=np.exp(lp)
  assert int(np.argmax(v))==out['argmax']
  max_error=max(max_error,abs(float(-(prob*lp).sum())-out['entropy_nats']))
  for key in ['newline','mata','gold']:
   t=out[key]['token']; z=out[key]
   max_error=max(max_error,abs(float(lp[t])-z['logP']),abs(float(prob[t])-z['P']))
   assert 1+int((v>v[t]).sum())==z['rank']
  assert [int(i) for i in np.argsort(-v,kind='stable')[:10]]==[z['token'] for z in out['top10']]
assert max_error<1e-10
for c in r['cases']:
 assert abs(c['delta']-(c['C']['gold']['logP']-c['U']['gold']['logP']))<1e-12
 assert c['position_ids']==list(range(c['input_length']))
ledger=[json.loads(t) for t in (P/'FORWARD_LEDGER.jsonl').read_text().splitlines()]
counts=Counter(z['event'] for z in ledger); assert counts=={'intent':80,'completed':80}
assert [(z['phase'],z['index'],z['kind']) for z in ledger if z['event']=='intent']==[(z['phase'],z['index'],z['kind']) for z in ledger if z['event']=='completed']
assert e['actual_optimizer_calls']==0 and e['actual_model_forward_calls']==80
for name,key in [('RESULTS.json','primary_result_sha256'),('AUXILIARY_RESULTS.json','auxiliary_result_sha256')]:assert sha((P/name).read_bytes())==e[key]
aux_summary=[]
for pos in range(8):
 cs=[c['conditions']['C'][pos] for c in a['cases']]; us=[c['conditions']['U'][pos] for c in a['cases']]
 ds=[c['gold']['logP']-u['gold']['logP'] for c,u in zip(cs,us)]
 aux_summary.append(dict(position=pos+1,positive=sum(d>0 for d in ds),mean_delta=statistics.mean(ds),NLL_C=statistics.mean(c['NLL'] for c in cs),NLL_U=statistics.mean(u['NLL'] for u in us),P_LF_C=statistics.mean(c['newline']['P'] for c in cs),P_LF_U=statistics.mean(u['newline']['P'] for u in us)))
selected=[(c['conditions']['C'][i],c['conditions']['U'][i]) for c in a['cases'] for i in range(1,8)]
content=[(c['conditions']['C'][i],c['conditions']['U'][i]) for c in a['cases'] for i in range(8) if c['conditions']['C'][i]['specific_content_piece']]
def pool(rows):
 ds=[c['gold']['logP']-u['gold']['logP'] for c,u in rows]
 return dict(n=len(ds),positive=sum(d>0 for d in ds),mean_delta=statistics.mean(ds),median_delta=statistics.median(ds),gold_argmax_C=sum(c['gold']['rank']==1 for c,u in rows),gold_argmax_U=sum(u['gold']['rank']==1 for c,u in rows))
summary=dict(primary=r['groups'],auxiliary_by_position=aux_summary,auxiliary_positions_2_to_8=pool(selected),specific_content_BPE_pieces=pool(content))
(P/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
verification=dict(passed=True,frozen_files_checked=len(f['sha256']),raw_vectors_checked=192,max_recomputed_numeric_error=max_error,ledger_intents=80,ledger_completed=80,optimizer_calls=0,additional_model_forwards=0,limitations='Archive verification does not independently validate model implementation or semantic understanding.')
(P/'VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n')
lines=['# 段落境界の文脈利用：比較表','', 'C＝正しい履歴、U＝別ページの無関係履歴。確率は全語彙softmax。Δは自然対数。32件は16対16の層別診断標本であり、学習分布の代表平均ではない。','', '|群|件数|Δ>0|平均Δ|中央値Δ|平均P(LF) C/U|平均P(また) C/U|平均正解順位 C/U|平均H C/U|','|---|---:|---:|---:|---:|---|---|---|---|']
for label,group in [('全体（均等抽出）',r['cases']),('また',[c for c in r['cases'] if c['group']=='mata']),('その他',[c for c in r['cases'] if c['group']=='other'])]:
 ds=[c['delta'] for c in group]
 def means(key,field):return '/'.join(f"{statistics.mean(c[k][key][field] for c in group):.5f}" for k in ['C','U'])
 hs='/'.join(f"{statistics.mean(c[k]['entropy_nats'] for c in group):.5f}" for k in ['C','U'])
 lines.append(f"|{label}|{len(ds)}|{sum(d>0 for d in ds)}|{statistics.mean(ds):.6f}|{statistics.median(ds):.6f}|{means('newline','P')}|{means('mata','P')}|{means('gold','rank')}|{hs}|")
lines += ['', '全64条件でargmax＝LF、また＝2位。argmaxの変更0/32。分位点・固定bin別分布・JSはRESULTS.jsonのgroupsに保存。','', '|ID|群|年度|長さ|正解BPE片|Δ|P(g) C/U|順位 C/U|P(LF) C/U|P(また) C/U|H C/U|','|---:|---|---:|---:|---|---:|---|---|---|---|---|']
for c in r['cases']:
 def pair(key,field):return '/'.join(f"{c[k][key][field]:.5f}" for k in ['C','U'])
 lines.append(f"|{c['index']}|{c['group']}|{c['year']}|{c['input_length']}|{c['gold_piece'].replace('|','&#124;')}|{c['delta']:.6f}|{pair('gold','P')}|{pair('gold','rank')}|{pair('newline','P')}|{pair('mata','P')}|{c['C']['entropy_nats']:.4f}/{c['U']['entropy_nats']:.4f}|")
lines += ['', '## 補助：同じ正解8tokensによるteacher forcing','', '|位置|Δ>0 /8|平均Δ|NLL C/U|P(LF) C/U|','|---:|---:|---:|---|---|']
for z in aux_summary:lines.append(f"|{z['position']}|{z['positive']}|{z['mean_delta']:.6f}|{z['NLL_C']:.5f}/{z['NLL_U']:.5f}|{z['P_LF_C']:.8f}/{z['P_LF_U']:.8f}|")
lines+=['','2–8位置：'+json.dumps(pool(selected),ensure_ascii=False),'','事前指定した具体内容BPE片：'+json.dumps(pool(content),ensure_ascii=False),'','|代表ID|群|第1位置Δ|第2–8位置の平均Δ|','|---:|---|---:|---:|']
for c in a['cases']:
 ds=[c['conditions']['C'][i]['gold']['logP']-c['conditions']['U'][i]['gold']['logP'] for i in range(8)]
 lines.append(f"|{c['index']}|{c['group']}|{ds[0]:.6f}|{statistics.mean(ds[1:]):.6f}|")
lines += ['','元文書・対応するU・全入力と位置はINPUT_PAIRS.json、全順位・上位10件と確率はRESULTS.json、補助の位置別結果はAUXILIARY_RESULTS.jsonを参照。']
(P/'TABLES.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(verification))
