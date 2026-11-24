import pathlib,json,hashlib
P=pathlib.Path(__file__).parent;read=lambda n:json.loads((P/n).read_text());s=read('SUMMARY.json');e=s['evaluations'];c=read('SOURCE_CONTRIBUTION.json');idx=read('CHECKPOINT_INDEX.json');nll=read('SOURCE_NLL.json')
lines=['# 数値比較','','同じ66入力・同じ順序を一巡。A/Bでloss対象が異なるためTRAIN lossの大小は直接の優劣ではない。','','| 保存点 | TRAIN返答本文NLL | DEV返答本文NLL | DEV本文＋EOS NLL |','|---|---:|---:|---:|']
for name in ['initial','A-pilot9','A-pilot17','B-pilot9','B-pilot17']:
 q=e[name]['NLL'];a=q['pilot_train'];b=q['dev'];lines.append(f"| {name} | {a if isinstance(a,float) else a['body_NLL']:.6f} | {b if isinstance(b,float) else b['body_NLL']:.6f} | {('未集計'if isinstance(b,float)else format(b['with_EOS_NLL'],'.6f'))} |")
lines+=['','| 指標 | 共通初期 | 全CE終端 | 返答CE終端 |','|---|---:|---:|---:|','| 新DEVの条件に沿う具体応答 | 0/15 | 0/15 | 0/15 |','| caption自然短文補完（旧基準） | 21/32（保存済み結果） | 21/32 | 21/32 |','| 新段落 | 0/5 | 0/5 | 0/5 |','| 展開文章 | 0/45 | 0/45 | 0/45 |','| 内容必須 | 0/24 | 0/24 | 0/24 |','| 資料付き | 0/23 | 0/23 | 0/23 |','| 自己履歴 | 0/4 | 0/4 | 0/4 |','| 新DEV EOS出現 | 15/15 | 13/15 | 13/15 |','| 新DEV repeated4gram proxy | 6/15 | 10/15 | 11/15 |','','EOS出現は内容・適切な終了の合格ではない。反復proxyは人間による有害反復率ではない。初期の旧評価を再推論していない。中間はNLLと生出力を保存し、意味採点は未実施。終端の選び直しなし。','','| TRAIN原資料 | 応答 | A全教師 | B本文 | B EOS | B全教師 |','|---|---:|---:|---:|---:|---:|']
for k,v in c.items():lines.append(f"| {k} | {v['responses']} | {v['full_A']} | {v['body_B']} | {v['EOS_B']} | {v['all_B']} |")
lines+=['','| 最適化 | 全CE | 返答CE |','|---|---:|---:|']
for k in ['retained','active_teachers','gradient_median','clip_count','update_delta_L2_sum','update_seconds']:lines.append(f"| {k} | {s['optimization']['A'][k]:.6f} | {s['optimization']['B'][k]:.6f} |")
lines+=['','deltaは各stepのL2変化の和であり初期→終端の距離ではない。重み変化を能力と同一視しない。全34保持更新でclip発生。','','| ASDC DEV部分資料 | 件数 | 本文tokens | 初期NLL | 全CE | 返答CE |','|---|---:|---:|---:|---:|---:|']
for source in ['main','vanilla','supplemental']:
 q=nll['initial']['dev'][source];lines.append(f"| {source} | {q['cases']} | {q['body_tokens']} | {q['body_NLL']:.6f} | {nll['A-pilot17']['dev'][source]['body_NLL']:.6f} | {nll['B-pilot17']['dev'][source]['body_NLL']:.6f} |")
lines+=['','| 全状態 | Adam step | SHA256 |','|---|---:|---|']
for q in idx['new_states']:lines.append(f"| {q['arm']}-{q['cursor']} | {q['Adam_steps'][0]} | `{q['sha256']}` |")
(P/'TABLES.md').write_text('\n'.join(lines)+'\n')
