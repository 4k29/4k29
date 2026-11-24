"""Prepare an unscored, anonymized review worksheet; never impersonate human evaluation."""
import pathlib,json,hashlib,random,csv
D=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def main():
 pieces=[bytes.fromhex(x)for x in read(D.parent/'data/tokenizer.json')['bytes']]
 entries=[]
 for model in ['A-6459','B-6459']:
  p=D/'evaluation'/f'{model}.json'
  for c in read(p)['cases']:
   if c['panel']=='train4':continue
   raw=b''.join(pieces[t]for t in c['prefix']if t>=6)
   entries.append(dict(model=model,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),id=c['id'],panel=c['panel'],prompt_utf8=raw.decode('utf8','strict'),output=c['text'],rawBytesHex=c['rawBytesHex'],eos=c['eos']))
 random.Random(71029).shuffle(entries)
 out=D/'blind-review';out.mkdir(exist_ok=True);key={};public=[]
 for i,e in enumerate(entries):
  sid=f'blind-{i:03d}';key[sid]={k:e[k]for k in ['model','source_sha256','id','panel']}
  public.append(dict(sample_id=sid,prompt=e['prompt_utf8'],generated_full_text=e['output'],rawBytesHex=e['rawBytesHex'],EOS=e['eos']))
 (out/'samples.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
 (out/'assignment-key.json').write_text(json.dumps(key,ensure_ascii=False,indent=2)+'\n')
 with(out/'worksheet.csv').open('w',newline='')as f:
  w=csv.writer(f);w.writerow(['sample_id','grammar_0_1_2','full_semantic_coherence_0_1_2','context_connection_0_1_2','new_content_beyond_prefix_0_1_2','harmful_repetition_yes_no','appropriate_end_yes_no','whole_success_yes_no','reason','reviewer_id'])
  for e in public:w.writerow([e['sample_id']]+['']*9)
 (out/'README.md').write_text('''# 未採点の盲検評価準備資料

実際の独立評価者・評価回答は **0件**。メインassistantが既に読んだ研究DEVを匿名化した準備物で、新規TESTや独立人間評価を実施した証拠ではない。assignment-key.jsonを評価者へ渡さず、worksheetを独立した日本語母語話者が記入する。生成文やraw bytesを修正しない。

文法、全文の意味、入力とのつながり、追加内容をそれぞれ0=不成立/1=部分的/2=成立で採点し、主述・修飾・活用・文間接続・主題逸脱・事実の疑いを理由欄へ書く。反復と自然な終了は別項目とし、EOSがあるだけで合格にしない。疑似語、意味破綻、有害な反復がある全文は合格にしない。短い正しい文末補完はその旨を記し、新たな段落や対話の能力と区別する。参照文との文字列差だけで誤りにせず、参照自体の単純化・時点依存も考慮する。

この採点表は既存の研究ゲートや正式17/13/9等の採用条件を変更しない。評価者間の不一致は原票を保持して別途検討する。モデルIDを推測できる表現差があるため、匿名化が完全な盲検を保証するわけではない。
''')
 print('Prepared',len(public),'unscored samples; independent human responses=0')
if __name__=='__main__':main()
