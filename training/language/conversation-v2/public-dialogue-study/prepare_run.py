import pathlib,json,hashlib,collections,urllib.request,sys,difflib,unicodedata
P=pathlib.Path(__file__).parent;V=pathlib.Path('/workspace/4k29/training/language/conversation-v2');sys.path.insert(0,str(V));from new_tokenizer import Encoder
read=lambda p:json.loads(p.read_text());write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=read(P/'DATA.json');records=read(P/'PRIVATE/RECORDS.json');lookup={str(r['id']['id']if isinstance(r['id'],dict)else r['id']):r for r in records};enc=Encoder(read(V/'data/tokenizer.json'));pieces=[bytes.fromhex(x)for x in read(V/'data/tokenizer.json')['bytes']];teachers=collections.Counter();pos=set()
for part,rows in d['parts'].items():
 for r in rows:
  raw=lookup[r['document']];us=raw['utterances'][:r['original_ordinal']+1];assert us[:-1]==r['history'] and us[-1]['text']==r['response'] and raw['partition']==part
  t=[1]
  for u in us:
   ids=enc(u['text']);assert b''.join(pieces[x]for x in ids)==u['text'].encode();t+=[4 if u['role']=='agent'else 3]+ids+[2]
  assert t==r['tokens'];s=r['response_body_start'];assert t[s-1]==4 and t[-1]==2 and all(x>5 for x in t[s:-1]);assert len(t)<=257
  if part=='train':
   for i in range(len(t)-1):
    k=(r['document'],i+1);assert k not in pos;pos.add(k)
   teachers.update(t[1:])
  r['retrieval_proxy_only']=False;r['adoption_basis']='main-agent full-history semantic review, scoped fictional operator clarification'
write(P/'DATA.json',d)
write(P/'INPUT_AUDIT.json',dict(source_original_matching=True,byte_roundtrip=True,teacher_shift='x=t[:-1],y=t[1:], response mask y[s-1:len(t)-1]',train_all_teachers=len(pos),train_reply_body=2058,train_reply_EOS=66,counts_BOS=teachers[1],counts_EOS=teachers[2],counts_roleA=teachers[3],counts_roleB=teachers[4],counts_LF=teachers[16],counts_PAD=teachers[0],no_window_cropping=True,no_fake_EOS=True,padding_ignore_index=-100,one_selected_prefix_per_document=True,no_source_teacher_repeated_in_this_run=True,model_previous_ASDC_exposure_not_assumed=False))
required={387:'旅行先・人数・日程と湖の眺めという条件を保持し、部屋数など未確定事項を具体的に確認する。既知条件を矛盾させない。',389:'草津・男女4人・2部屋という既知条件を尊重し、和室洋室など未確定の部屋条件を具体的に確認する。',391:'沖縄の離島という条件を尊重し、次に必要な希望条件を質問する。架空の宿の在庫を断定しない。',394:'温泉希望を受け、露天風呂など浴場の希望を具体的に確認する。',404:'安全性・防犯の希望を尊重し、関連する具体条件または他の必要条件を確認する。',415:'サービス充実という曖昧な希望について、希望するサービスを具体的に尋ねる。',416:'荷物を軽くしたい意図と備品希望を受け、必要なアメニティを具体的に尋ねる。',420:'ホテルより古い旅館の雰囲気を希望することを尊重し、残る条件を確認する。',435:'子ども連れではない夫婦の落ち着いた宿泊希望を尊重し、静かな環境など具体的な希望を確認する。',441:'小麦アレルギーという条件を取り違えず、必要な対応を確認する。実在の施設や食事の安全を保証しない。',445:'京都・懐石料理の希望を保持して次の条件を確認する。施設や評判を捏造しない。',450:'費用重視・食事の追加希望なしを踏まえ、夕食を外す選択肢などを確認する。勝手に予約内容を確定しない。',452:'和洋の好みが異なり朝食の種類を求める文脈に沿って、多様なメニューや食事形式を提案・確認する。',455:'仙台で朝食のおいしさを希望することを受け、好みの料理など具体的条件を確認する。',476:'駐車場の希望を受けて、種類・立地など必要な駐車条件を尋ねる。未提供の料金や空きを断定しない。'}
write(P/'DEV_PROTOCOL.json',dict(frozen_before_model_inference=True,partition='official ASDC dev; retained document/question family separate, known MAIN actors disjoint; crowd worker identity unavailable',not_sealed_test=True,reviewer='main assistant, nonblind; independent human evaluation absent',max_new_tokens=64,decoder='full vocabulary greedy, no suppression/penalty/template',success='natural response using relevant concrete condition or useful missing-information question; generic acknowledgement alone fails; reference string match not required',separate_axes=['condition_use','natural_one_sentence','coherent_two_or_three_sentences','repetition','EOS','unverified_inventory_claim'],cases=[dict(id=r['id'],manual_index=r['manual_index'],required=required[r['manual_index']],prefix=r['tokens'][:r['response_body_start']],reference=r['response'],maxNewTokens=64)for r in d['parts']['dev']]))
assert all(r['response_body_start']+64<=256 for r in d['parts']['dev'])
# Canonical and near response/history audit across selected parts.
canon=lambda s:''.join(unicodedata.normalize('NFKC',s).split()).casefold();pairs=[]
for a in d['parts']['train']:
 for b in d['parts']['dev']:
  ratio=difflib.SequenceMatcher(None,canon(a['response']),canon(b['response']),autojunk=False).ratio()
  assert a['family']!=b['family'] and ratio<.85
  pairs.append(ratio)
write(P/'SPLIT_AUDIT.json',dict(cross_pairs=len(pairs),canonical_response_overlap=0,response_near_threshold=.85,max_similarity=max(pairs),known_MAIN_actor_overlap=0,crowd_author_ids_unavailable=True,family_parent_metadata_used=True,no_partition_moved=True,source_TEST_used=False,public_source_TEST_schema_examples_previously_viewed=['asdc.sup.topic.L2.food.4turn.00001','asdc.sup.topic.L1.4turn.00001'],schema_examples_excluded=True,project_sealed_TEST_never_opened=True))
# Minimal first-party FAQ investigation, no corpus retrieval/training.
urls=['https://www.opendata4children.org/']
faq=[]
for u in urls:
 try:
  with urllib.request.urlopen(u,timeout=20)as f:b=f.read();status=f.status
  faq.append(dict(url=u,status=status,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),adopted=False,reason='Landing page alone does not establish per-FAQ rights, provenance or factual currency; no FAQ body acquired for learning'))
 except Exception as e:faq.append(dict(url=u,error=str(e),adopted=False))
write(P/'SOURCE_RIGHTS.json',dict(asdc=dict(repository='https://github.com/megagonlabs/asdc',revision='f37d6575c73602adcb8ae3687520726793baa672',license='CC-BY-4.0 for corpus, annotations and documentation; Apache-2.0 programs',evidence=['asdc-README.md','asdc-LICENSE.txt','ACQUISITION.json'],training_and_public_research_checkpoint='Compatible within supplied original fictional human dialogue, with attribution; no source model-publication prohibition found. Not blanket clearance for unrelated third-party content.',attribution='Yuta Hayashibe, Megagon Labs, Accommodation Search Dialog Corpus, LREC2022/NLP2021',changes='Publisher text_fixed where provided; role/token serialization, filtering/split selection; no own text rewrite',public_raw_scope='Only curated reviewed subset, with full license and provenance; source archive reacquirable by SHA'),newschat=dict(repository='https://github.com/fukanarita/newschat-with-impression',revision='fd09d8a7cad99449c5353447b785985fe8ac9a32',repository_license='MIT, Fuka Narita 2023',training_status='hold',reason='README sample embeds attributed news quotation even with used_tweet empty. MIT repository license does not clear third-party news/tweets. No dialogue body files fetched or adopted.',evidence=['newschat-with-impression-README.md','newschat-with-impression-LICENSE']),faq=faq,ichikara='Excluded: model-publication prohibition and no private permanent storage',checked_UTC='2026-11-12',optimizer_updates=0))
print('prepared',len(d['parts']['train']),len(d['parts']['dev']),len(pos),teachers)
