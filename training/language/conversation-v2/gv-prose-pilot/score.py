import pathlib,json,hashlib,collections
P=pathlib.Path(__file__).resolve().parent;read=lambda p:json.loads(pathlib.Path(p).read_text());write=lambda f,d:(P/f).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
manual=read(P/'PROSE_MANUAL_LABELS.json')['labels'];base=read(P/'BASE_CAPTION_DECISIONS.json');ds={k:read(P/'evaluation'/f'{k}.json')for k in ['initial','B-terminal','C-terminal']};old={r['id']:r for r in ds['initial']['cases']};pieces=[bytes.fromhex(x)for x in read(P.parent/'data/tokenizer.json')['bytes']]
results={};counts={}
for name,d in ds.items():
 rows=[]
 for r in d['cases']:
  caption=r['panel']=='new-caption32';id=r['id'];a=old[id];equal=r['tokensIncludingEos']==a['tokensIncludingEos'];h=hashlib.sha256(json.dumps(r['tokensIncludingEos']).encode()).hexdigest()
  if not caption:
   if not r['nonEosTokens']:why='即時EOSで新しい本文が0。提示済みprefixを成功へ加算しない。'
   elif ' ' * 16 in (r['text']or''):why='水素等の断片から長い空白列へ崩壊。意味のつながる本文になっていない。'
   elif '「「「'in(r['text']or''):why='括弧記号の長い反復で本文・話題の説明が成立しない。'
   else:why='全文を読解。疑似語・同語句・数字・構文の有害反復が続き、入力に沿う意味的な複数文が成立しない。'
   rows.append(dict(id=id,panel=r['panel'],generated_tokens_SHA=h,**manual[name][id],reason=why,review='main assistant full raw continuation reading; not reference exact-match scoring'))
   continue
  dec=dict(base[id]);method='reused prior identical-input/output judgment'if equal else'main assistant reading of changed complete prefix+continuation, same conservative criterion'
  if name=='B-terminal'and id=='stair:468221':dec.update(decision='uncertain_not_passed',reason='並んだノートパソコン上に白いバイクを置くという物理的関係が不自然で保守的に不合格。')
  elif name=='C-terminal'and id=='stair:468221':dec.update(decision='fail',reason='並んだ3台のノートパソコンの前にある、で終わり、何があるかという主語がなく独立した場面文が成立しない。')
  elif name=='C-terminal'and id=='stair:771030':dec.update(decision='natural_short_text_only',reason='ツヤのある床の上に白い犬がいる、という自然な場面短文。画像真偽・段落能力の主張ではない。')
  elif name=='C-terminal'and id=='stair:689478':dec.update(decision='natural_short_text_only',reason='2つのドアの前に白いシャツが置かれている、という成立する短文。新しい物体の画像上の真偽は未評価。')
  elif not equal and dec['decision']=='natural_short_text_only':dec['reason']='元のprefixと無修正継続が短い場面文として成立する。追加の対象や動作の画像真偽は評価していない。段落・内容応答の成功ではない。'
  if name=='B-terminal'and id=='stair:363439':dec['reason']='サーフボードを持った男性がさらにスケートボードを持つことは物理的に可能な短文。ただし冗長で追加物体の真偽は未検証。'
  if name=='C-terminal'and id=='stair:314944':dec['reason']='ウエイトレスの女性がテーブルを持っている、は机を運ぶ等の成立する短文。画像真偽や適切な接客行動は未評価。'
  try:whole=b''.join(pieces[t]for t in r['prefix']+r['nonEosTokens']).decode('utf8')
  except UnicodeDecodeError:whole=None
  rows.append(dict(id=id,panel=r['panel'],generated_tokens_SHA=h,same_generated_tokens_as_initial=equal,whole_prefix_plus_output=whole,**dec,review=method))
 results[name]=rows
 cap=[x for x in rows if x['panel']=='new-caption32'];prose=[x for x in rows if x['panel']!='new-caption32'];passed={x['id']for x in cap if x['decision']=='natural_short_text_only'};oldpassed={k for k,v in base.items()if v['decision']=='natural_short_text_only'}
 counts[name]=dict(caption_natural=len(passed),caption_initial21_retained=len(passed&oldpassed),caption_new=sorted(passed-oldpassed),caption_regressed=sorted(oldpassed-passed),caption_ending_or_noun_completion=sum(x['decision']=='natural_short_text_only'and x['ending_only_or_supplied_noun_completion']for x in cap),caption_changed_token_sequences=sum(not x['same_generated_tokens_as_initial']for x in cap),paragraph_new6=sum(x['connected_2to3_new_sentences']for x in prose if x['panel']=='fixed-new6'),paragraph_old12=sum(x['connected_2to3_new_sentences']for x in prose if x['panel']=='fixed-prose12'),prose_harmful_repetition=sum(x['harmful_repetition']for x in prose),prose_appropriate_EOS=sum(x['appropriate_EOS']for x in prose))
write('SEMANTIC_REVIEW.json',dict(method='nonblind single main assistant; no independent native-human judge',prior_caption_source='mixed-retention-study/terminal-MIX-CAPTION_DECISIONS.json@bb9310d36fce16cb6b190eeedb26d947c8af66ad',prior_caption_SHA=hashlib.sha256((P/'BASE_CAPTION_DECISIONS.json').read_bytes()).hexdigest(),rubric='EVALUATION_INPUTS.json fixed before optimizer; captions score complete prefix+continuation, paragraphs require newly generated connected sentences; no image truth claim',cases=results,counts=counts))
print(json.dumps(counts,ensure_ascii=False,indent=2))
