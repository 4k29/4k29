"""Data and extraction regressions only. No Torch/model import, forward or optimizer."""
import pathlib,sys,json,gzip,hashlib,unittest
P=pathlib.Path(__file__).resolve().parent;V=P.parent;sys.path.insert(0,str(P/'acquisition'));sys.path.insert(0,str(V));from new_tokenizer import Encoder
from extract import extract
from gv_extract import paragraphs
load=lambda f:json.loads((P/f).read_text())
def wiki(text):return dict(site='ja.wikibooks.org',pageid=99999999,title='TEST ONLY',revision=dict(revid=1,timestamp='2020-01-01T00:00:00Z',user='test',comment='fixture',slots=dict(main={'*':text})),license='unit fixture, not TRAIN',retrieved_UTC='fixture')
class Study(unittest.TestCase):
 def test_math_removal_never_salvages_partial_paragraph(self):
  raw='式<math>x</math>は対象の値です。説明の後半です。\n\nこれは独立した検査用の文章であり、実際の学習用原文ではありません。完全な段落が保持されることだけを確認します。別の内容を補って自然文を作ることはしません。'
  r=extract(wiki(raw));self.assertEqual(len(r),1);self.assertFalse('は対象'in r[0]['text']);self.assertIn('独立した',r[0]['text'])
 def test_unknown_inline_template_excludes_whole_original_paragraph(self):
  raw='対象{{unknown|欠落}}に関する途中の説明です。後ろの文だけを拾ってはいけません。';self.assertEqual(extract(wiki(raw)),[])
 def test_no_join_across_heading_or_omitted_block(self):
  a='これは文の連続順序を確認するためだけに作成した試験専用の第一文であって学習には使用しません。';b='これは文の連続順序を確認するためだけに作成した試験専用の第二文であって学習には使用しません。'
  self.assertEqual(len(extract(wiki(a+'\n\n'+b))),1)
  self.assertEqual(extract(wiki(a+'\n\n== 別節 ==\n\n'+b)),[])
  self.assertEqual(extract(wiki(a+'\n\n{{image}}\n\n'+b)),[])
 def test_gallery_text_never_becomes_prose(self):
  raw='<gallery>\n\nここには検証用の除外すべき長い文章があります。画像の付属説明だけが段落として救出されることを禁止します。\n\n</gallery>';self.assertEqual(extract(wiki(raw)),[])
 def test_GV_quote_barrier_and_missing_credit(self):
  # Synthetic parser fixtures only; never source/teacher data.
  a='この文章は機械的な検証のためだけに用意した独立した長めの文章です。実際の人間執筆資料として扱わず、モデルに渡される学習原文にも決して含めません。長さの下限を満たす試験入力として使います。'
  b='別の段落では、元の文の順番を勝手につなげないことを機械的に確かめます。この文は独立した単体試験の固定文字列であり、実際に収集した記事の本文ではありません。二つの段落の間に別の要素がある場合を試験します。'
  d=dict(id=99999999,status='publish',date_gmt='2020-01-01',modified_gmt='2020-01-01',link='https://jp.globalvoices.org/fixture-only/',title=dict(rendered='TEST ONLY'),content=dict(rendered='<p>'+a+'</p><blockquote><p>EXCLUDED THIRD PARTY FIXTURE</p></blockquote><p>'+b+'</p>'))
  w=b'<div id="post-header-credit"><div class="contributor-name"><span class="credit-label">reporter</span><a class="user-link" href="https://globalvoices.org/author/test/">A</a></div></div>'
  self.assertEqual(paragraphs(d,w),[])
  w='<div id="post-header-credit"><div class="contributor-name"><span class="credit-label">記者</span><a class="user-link" href="https://globalvoices.org/author/test/">A</a></div><div class="contributor-name"><span class="credit-label">翻訳</span><a class="user-link" href="https://jp.globalvoices.org/author/test/">B</a></div></div><span class="post-translation-en"><a href="https://globalvoices.org/2020/test/">English</a></span><a href="https://creativecommons.org/licenses/by/3.0/">CC</a>'.encode()
  rr=paragraphs(d,w);self.assertEqual(len(rr),2);self.assertTrue(all('EXCLUDED'not in r['text']for r in rr));self.assertTrue(all(len(r['source_span_positions'])==1 for r in rr))
 def test_admitted_UTF8_tokenization(self):
  t=json.loads((V/'data/tokenizer.json').read_text());self.assertEqual(len(t['bytes']),3997);enc=Encoder(t);pp=[bytes.fromhex(x)for x in t['bytes']];self.__class__.rows=[json.loads(s)for s in gzip.decompress((P/'REVIEWED_PROSE.jsonl.gz').read_bytes()).splitlines()]
  for r in self.rows:
   self.assertEqual([1]+enc(r['text'])+([2]if r['EOS']else[]),r['tokens']);self.assertEqual(b''.join(pp[k]for k in r['tokens']if k>=6),r['text'].encode());self.assertEqual(hashlib.sha256(r['text'].encode()).hexdigest(),r['text_SHA']);self.assertFalse(any(a==b==16 for a,b in zip(r['tokens'],r['tokens'][1:])))
 def test_unique_teacher_shift_and_no_fake_EOS(self):
  rows=[json.loads(s)for s in gzip.decompress((P/'REVIEWED_PROSE.jsonl.gz').read_bytes()).splitlines()];seen=set()
  for z in load('SCHEDULE.json')['windows']:
   t=rows[z['record']]['tokens'];a=z['input_start'];end=z['end'];x=t[a:end-1];y=t[a+1:end];self.assertEqual(x[1:],y[:-1]);self.assertLessEqual(len(x),256)
   for k in range(z['target_start'],end):self.assertNotIn((z['record'],k),seen);seen.add((z['record'],k))
  self.assertEqual(len(seen),2767);self.assertEqual(sum(t==2 for r in rows for t in r['tokens']),0)
 def test_GV_attribution_and_provenance(self):
  rows=[json.loads(s)for s in gzip.decompress((P/'REVIEWED_PROSE.jsonl.gz').read_bytes()).splitlines()]
  for r in rows:
   if r['source'].startswith('globalvoices'):
    self.assertTrue(any('翻訳'in x['role']for x in r['attribution']));self.assertTrue(any('記者'in x['role']for x in r['attribution']));self.assertTrue(r['original_GV_URL'].startswith('https://globalvoices.org/'));sp=r['source_span_positions'];self.assertTrue(all(b['top_element']==a['top_element']+1 for a,b in zip(sp,sp[1:])));self.assertLess(r['revision'],'2022-01-01')
 def test_DEV_unchanged_and_family_disjoint(self):
  self.assertEqual(hashlib.sha256((P/'NEW_PROSE_DEV.json').read_bytes()).hexdigest(),'9b499701bcb5b497b9a9f66856abc1862a045dd6ec58287ab58dca9ce2468951');self.assertTrue(load('DEV_EXTRACTION_RECHECK.json')['passed']);dev={x['family']for x in load('NEW_PROSE_DEV.json')['cases']};rows=[json.loads(s)for s in gzip.decompress((P/'REVIEWED_PROSE.jsonl.gz').read_bytes()).splitlines()];self.assertFalse(dev.intersection(r['family']for r in rows))
 def test_no_training_or_new_checkpoint_claim(self):
  d=load('OPTIMIZER_LEDGER.json');self.assertEqual(d['actual_optimizer_calls'],0);self.assertEqual(d['model_forwards'],0);self.assertEqual((P/'UPDATES.jsonl').read_bytes(),b'');self.assertEqual((P/'FORWARDS.jsonl').read_bytes(),b'');self.assertEqual(load('CHECKPOINT_INDEX.json')['new_checkpoints'],[]);self.assertFalse(load('PLAN.json')['training_GO'])
 def test_plan_integrity(self):
  plan=load('PLAN.json');root=V.parents[2]
  self.assertEqual(hashlib.sha256((P/'PLAN.json').read_bytes()).hexdigest(),(P/'PLAN.sha256').read_text().strip())
  for n,h in plan['sha256'].items():self.assertEqual(hashlib.sha256((root/n).read_bytes()).hexdigest(),h,n)
if __name__=='__main__':unittest.main()
