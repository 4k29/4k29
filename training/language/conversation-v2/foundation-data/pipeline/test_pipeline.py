import hashlib,json,pathlib,tempfile,unittest
from build import Union,book_family,canonical,ingest_jaquad,near_pairs,norm,split
from wiki_adapter import prose

class PipelineTests(unittest.TestCase):
 def test_normalization_is_not_semantic_nfkc_or_raw_mutation(self):
  original='Ａさん\r\ne\u0301 の説明。'
  self.assertEqual(norm(original),'Ａさん\né の説明。')
  self.assertNotEqual(canonical('Ａ'),canonical('A'))
  self.assertEqual(original,'Ａさん\r\ne\u0301 の説明。')
 def test_transitive_family_component_has_one_split(self):
  u=Union(['jaquad|B','jaquad|A','jawikibooks|本']);u.join('jaquad|B','jawikibooks|本');u.join('jaquad|A','jaquad|B')
  self.assertEqual(len({split(u.find(k))for k in u.parent}),1)
  self.assertEqual(u.find('jawikibooks|本'),'jaquad|A')
 def test_clear_law_sections_join_book_without_slash(self):
  self.assertEqual(book_family('刑事訴訟法第187条の2'),'刑事訴訟法')
  self.assertEqual(book_family('刑事訴訟法第490条'),'刑事訴訟法')
  self.assertEqual(book_family('刑事訴訟法'),'刑事訴訟法')
  self.assertEqual(book_family('国民年金法施行規則第6条の3'),'国民年金法施行規則')
  self.assertEqual(book_family('〇〇施行令第七条'),'〇〇施行令')
  self.assertEqual(book_family('数学/数学的帰納法'),'数学')
  self.assertEqual(book_family('C++/関数'),'C++')
 def test_near_retrieval_verifies_jaccard_not_just_common_phrase(self):
  base='日本語の文章の品質を検証します。段落の主語と述語が対応していることを確かめます。内容を改変せずに原典を保存します。出典の版と利用条件を記録します。各資料を文書単位で分割します。'
  similar=base+'説明。';other='日本語の文章の品質を検証します。'+'今日は海岸で魚を観察して動物の種類や生息地域を研究しています。'*4
  pairs,r=near_pairs([base,similar,other]);self.assertTrue(any(a==0 and b==1 for a,b,_ in pairs));self.assertFalse(any(b==2 for _,b,_ in pairs));self.assertFalse(r['exhaustiveNearOrSemanticDedup'])
 def test_source_corruption_and_qa_offset_rejected(self):
  with tempfile.TemporaryDirectory(dir='/dev/shm')as temp:
   p=pathlib.Path(temp);source=p/'source.json';source.write_text(json.dumps({'data':[{'title':'題','paragraphs':[{'context':'原文','qas':[{'id':'q','answers':[{'answer_start':1,'text':'原'}]}]}]}]}))
   row=dict(part=0,url='https://example.invalid/train',rawPath=str(source),bytes=source.stat().st_size,sha256=hashlib.sha256(source.read_bytes()).hexdigest());m=p/'manifest.json';m.write_text(json.dumps(dict(revision='fixed',shards=[row])))
   with self.assertRaisesRegex(ValueError,'offset'):ingest_jaquad(m)
   source.write_text('corrupt')
   with self.assertRaisesRegex(ValueError,'source'):ingest_jaquad(m)
 def test_templates_do_not_splice_invisible_missing_subject(self):
  text='この段落は{{hidden|重要な主語}}について説明しており、普通の日本語として読める長さを持っています。\n\n別の段落では、資料の出典や利用条件を確認し、原文に変更を加えず記録する方法を詳しく説明しています。'
  rows,stats=prose(text);self.assertEqual(len(rows),1);self.assertIn('別の段落',rows[0]);self.assertEqual(stats['blocksRejectedRemovedNode'],1)
 def test_reference_removed_but_answer_text_not_repaired(self):
  text='これは出典のある現代日本語の説明文です。文章の意味を保ちながら、段落の内容をそのまま記録します。<ref>引用の注記</ref>原文自体の言い換えは行いません。'
  rows,stats=prose(text);self.assertEqual(rows,[text.replace('<ref>引用の注記</ref>','')]);self.assertGreater(stats['nonproseTagsRemoved'],0)

if __name__=='__main__':unittest.main()
