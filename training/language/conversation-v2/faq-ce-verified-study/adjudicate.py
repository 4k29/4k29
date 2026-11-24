"""Serialize the MAIN agent's nonblind full-output readings; not an automatic semantic judge."""
import pathlib,json,hashlib,collections
P=pathlib.Path(__file__).resolve().parent;V=P.parent;rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
B0=V/'faq-ce-study/BASELINE-terminal-MIX.json'; BR=V/'faq-ce-study/BASELINE-terminal-MIX-READING.json'
if not B0.exists():
 B0=pathlib.Path(__import__('os').environ.get('V2_ROOT',V))/'mixed-retention-study/evaluation/terminal-MIX.json';BR=B0.with_name('terminal-MIX-READING.json')
base=rd(BR);baseline={x['id']:x for x in base['rows']if x['panel']=='new-caption32'};passed={k for k,x in baseline.items()if x['caption_natural']};minimal={k for k,x in baseline.items()if x['ending_only_or_supplied_noun_completion']};assert len(passed)==21
req={x['id']:x['required']for x in rd(P/'DEV_PROTOCOL.json')['cases']+rd(P/'GROUNDED_DEV.json')['cases']}
capfail={'40291':'金色のプレート上の白いバスは場面・尺度の整合を確認できない。旧基準でも保留。','325845':'Aは条件と水の崩れ、Bは鳥に2頭という不自然な数え方。','771030':'赤いバナナの場面を自然な具体的補完として確定できない。旧の白いバナナと同じ保守基準。','522263':'ニ＋ーボードで語を正しく補完できない。','91227':'ジャンパースの語境界と場面が崩れる。','746796':'猫がすっ＋ぽい皿という不自然な係り受け。','468221':'並んだ3台のノートパソコンの上に置かれている、は置かれた対象が欠けている。','414909':'ジュースの入ったピッ＋ターが不自然な語。','689478':'ドア前に置かれたバスの場面は旧基準の保留を維持。','822181':'Aは小さなパソコン横の白いバスで尺度・場面の整合が不明。Bは白い犬で自然。','17039':'ゾウが顔と鼻を柵の上に向いている、の格関係が不自然。','117870':'シマウマが一頭木のキリン…で対象・語順が破綻。','343877':'厨房の寸胴体がついている、という不自然な語と場面。'}
for arm in'AB':
 path=P/f'evaluation/{arm}-study93.json';e=rd(path);rows=[]
 for x in e['cases']:
  i,g=x['id'],x['panel'];caption=g=='new-caption32';success=caption and i in passed and i!='stair:468221'and not(arm=='A'and i=='stair:822181');held=arm=='A'and i=='v2-content-dev-010';reason=''
  if caption:reason=('入力の対象を保ち自然な短文補完。画像の事実一致や未知画像理解の成功ではない。'if success else capfail.get(i.split(':')[-1],'旧基準の自然さを満たすと確認できない。'))
  elif i in req:reason='必要情報：'+req[i]+' 生成はこれを答えず、無関係な内容・疑似語・反復へ逸脱。原文と異なるだけではなく必要事実が欠ける。'
  elif g in['old24','oldNew9','new-MAFF12','new_source_heldout_paragraph5']:reason='全prefixと全文を確認。反復・空白・疑似語・主題逸脱または語尾だけで、新たな意味のつながる2〜3文は成立しない。'
  elif g=='provided23':reason='入力された施設・料金・地域等の必要情報を使わず、実施設/国際/数字等の反復へ逸脱。資料参照の成功とは認めない。'
  elif g=='ASDC-condition-dev15':reason='希望条件に合う具体的確認・回答がなく、相槌のみ、無関係な話題、反復または不自然な文章。'
  else:reason=('「最近のゲームを見ます」は文として読める可能性があるが、作品を尋ねる文脈に十分な具体回答か確定できず保留。参照と不一致だけを理由にしない。'if held else'実際の問い・先行発話に必要な具体内容を返さず、相槌、無関係な問い返し、反復または意味の崩れ。')
  readable=bool(success or (x['text']or'').strip()in{'そうなんですね。','はい、夜はどうですか？','夏はどうですか？','お昼はどうですか？','最近、お話しますか？','最近のゲームを見ます。','はい、夏休みの日は雨が降ります。','夏は雨の日は雨が降ります。','お盆は行きましたか？'})
  rows.append(dict(id=i,panel=g,decision='pass_caption_only'if success else'hold'if held else'fail',caption_natural=success,ending_only_or_supplied_noun_completion=caption and i in minimal,concrete_response_success=False,coherent_new_2to3_sentences=False,readable_single_sentence_or_completion=readable,EOS_token=x['eos'],repeat4gram_proxy=bool(x['repeated4gram']),syntactically_appropriate_ending=readable and x['eos'],task_appropriate_ending=success and x['eos'],reason=reason,method='Main assistant nonblind full prefix and full generation reading; exact-repeat display compression only, raw unchanged'))
 episodes=[dict(id=z['id'],success=False,turns_actually_generated=sum('tokensIncludingEos'in t for t in z['turns']),reason='初回から必要な比較/行先/食事条件を満たさない。EOSが出ず後続へ進めない例と、3ターン出ても自己履歴の内容がつながらない例を区別。')for z in e['self_history']]
 out=dict(name=arm+'-study93',source_sha256=sha(path),reviewer='main Codex assistant only; no independent human evaluator or subagent',independent_native_human_evaluation=False,reference_exact_match_required=False,rows=rows,self_history=episodes,caption_natural=sum(r['caption_natural']for r in rows),caption_ending_heavy=sum(r['caption_natural']and r['ending_only_or_supplied_noun_completion']for r in rows),caption_initial21_retained=sum(r['caption_natural']and r['id']in passed for r in rows),caption_new_success=[r['id']for r in rows if r['caption_natural']and r['id']not in passed],caption_regressed=[i for i in sorted(passed)if not next(r['caption_natural']for r in rows if r['id']==i)],FAQ_dev_success=0,grounded_success=0,paragraph5_success=0,developed45_success=0,native24_strict_success=0,native24_hold=sum(r['decision']=='hold'for r in rows if r['panel']=='native24'),provided23_success=0,ASDC15_success=0,self_history_success=0)
 (P/f'evaluation/{arm}-study93-READING.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(arm,out['caption_natural'],out['caption_regressed'])
# Item-by-item caption retention; direct raw outputs from all3 models, not just aggregate count.
braw={r['id']:r for r in rd(B0)['cases']};arms={a:{r['id']:r for r in rd(P/f'evaluation/{a}-study93.json')['cases']}for a in'AB'}
compare=[]
for i in baseline:
 compare.append(dict(id=i,initial_pass=i in passed,initial_text=braw[i]['text'],ending_heavy=i in minimal,A_text=arms['A'][i]['text'],B_text=arms['B'][i]['text'],A_pass=i in passed and i not in['stair:468221','stair:822181'],B_pass=i in passed and i!='stair:468221',A_tokens_identical_to_initial=arms['A'][i]['tokensIncludingEos']==braw[i]['tokensIncludingEos'],B_tokens_identical_to_initial=arms['B'][i]['tokensIncludingEos']==braw[i]['tokensIncludingEos']))
(P/'CAPTION_COMPARISON.json').write_text(json.dumps(dict(initial_source_SHA=sha(B0),initial_reading_SHA=sha(BR),rows=compare,independent_human_evaluation=False),ensure_ascii=False,indent=2)+'\n')
# New initial cases were read too; retain the same content rubric, no claim of generation competence.
ip=P/'evaluation/initial.json';ie=rd(ip);(P/'evaluation/initial-READING.json').write_text(json.dumps(dict(source_sha256=sha(ip),reviewer='main assistant nonblind',independent_native_human_evaluation=False,rows=[dict(id=x['id'],panel=x['panel'],content_success=False,reason='必要事実を答えず、相槌・無関係な内容・反復または不自然な語へ逸脱。原文完全一致を要求した判定ではない。')for x in ie['cases']]),ensure_ascii=False,indent=2)+'\n')
