import json,pathlib
P=pathlib.Path(__file__).resolve().parent
s=json.loads((P/'SUMMARY.json').read_text());states=['A-base','B-base','SFT-A-93','SFT-B-93'];src=json.loads((P/'SOURCE_AUDIT.json').read_text())
lines=['# 固定終端の比較','', '| 状態 | FAQ DEV本文NLL | 文章DEV本文NLL | caption自然候補 | FAQ | 新文章2〜3文 | 文章DEV EOS | 反復proxy |','|---|---:|---:|---:|---:|---:|---:|---:|']
for k in states:
 a=s[k];c=a['panels']['new-caption32'];p=a['panels']['source-heldout-prose12'];lines.append(f"| {k} | {a['FAQ']['dev']['body_NLL']:.6f} | {a['prose_body_NLL']:.6f} | {c['strict_success']}/32 | 0/19 | 0/12 | {p['EOS']}/12 | {p['repeated4gram_proxy']}/12 |")
lines+=['','SFT-B captionは17件確認＋別に1件保留（stair:322805）。独立母語話者・盲検評価ではない。反復proxyは意味判定と別。新文章は元の第1文をprefixに含むが、提示文を生成成功へ加算しない。','','## 固定source DEV（本文のみ）','','| source | targets | A-base | B-base | A-SFT | B-SFT |','|---|---:|---:|---:|---:|---:|']
for k,z in s['A-base']['source_NLL'].items():lines.append('| '+k+' | '+str(z['targets'])+' | '+' | '.join(f"{s[n]['source_NLL'][k]['NLL']:.6f}"for n in states)+' |')
lines+=['','同じ530窓、53,847本文位置。露出済み開発診断であり独立TESTではない。EOS/LF/roleを除外する集計は推論語彙の抑制ではない。','','## 追加基盤原文（既存再利用、新規取得0）','','| source | records | 有効teachers | 非LF本文 | EOS | role |','|---|---:|---:|---:|---:|---:|']
for k,z in src['final_sources'].items():lines.append(f"| {k} | {z['records']} | {z['all_targets']} | {z['body_nonLF']} | {z['EOS']} | {z['role']} |")
lines+=['','## 実更新と勾配','','| 系列 | 保持更新 | 有効teachers | 非PAD入力 | clip数 | 勾配norm中央値 | Adam step終端 |','|---|---:|---:|---:|---:|---:|---:|']
for k,z in s['training']['by_tag'].items():lines.append(f"| {k} | {z['updates']} | {z['active_teachers']} | {z['input_nonPAD']} | {z['clip_count']} | {z['gradient_norm_median']:.4f} | {z['Adam_step_last']} |")
lines+=['','保持1,250、捨て検証6、再開replay3、実optimizer呼出し1,259。model forward47,033（再利用した出力は含まない）。各SFTのteacher35,138＝本文34,766＋真EOS372。両条件は同一49,856入力tokens。','','## 個別生成判定','','全183件×4状態の入力ID・raw対応SHA・判定理由は `evaluation/*-READING.json`。全文・全token・raw bytes・停止理由は対応する `.json`。本文NLLの中間結果は `B-LM-mid.json`、`SFT-A-47.json`、`SFT-B-47.json`。終端を主結果として固定し、途中選択していない。']
(P/'TABLES.md').write_text('\n'.join(lines)+'\n')
