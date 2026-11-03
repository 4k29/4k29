import unittest
from paragraphs import Paragraphs,units
A='環境を守るために生活の中でできることがあります。使っていない照明を消すと電気の節約になります。無理なく続けられる方法を選ぶことが大切です。'
B='買い物には袋を持って出かける方法があります。繰り返し使うことでごみを減らせます。必要な品物を確かめてから出かけましょう。'
class Boundaries(unittest.TestCase):
 def parse(self,html,root='main'):
  p=Paragraphs(root);p.feed(html);p.finish();return units(p.events)[0]
 def test_empty_main_marker(self):
  r=self.parse('<div id="main"></div><h2>生活</h2><p>'+A+'</p><div id="footer"><p>'+B+'</p></div>');self.assertEqual(len(r),1);self.assertEqual(r[0]['text'],A)
 def test_figure_barrier(self):
  r=self.parse('<div id="main"></div><p>'+A+'</p><div class="figblock"><img src="x"></div><p>'+B+'</p>');self.assertEqual(len(r),2);self.assertFalse(r[0]['EOS']);self.assertNotIn(B,r[0]['text'])
 def test_quote_column_not_admitted(self):
  r=self.parse('<body><p>'+A+'</p><div class="column"><p>'+B+'</p></div></body>','legacy_body');self.assertEqual(len(r),1);self.assertFalse(r[0]['EOS'])
 def test_adjacent_order(self):
  r=self.parse('<body><p>'+A+'</p><p>'+B+'</p></body>','legacy_body');self.assertEqual(r[0]['text'],A+'\n\n'+B)
 def test_nested_script_blocks_whole_paragraph(self):
  self.assertEqual(self.parse('<body><p>'+A+'<script>bad()</script></p></body>','legacy_body'),[])
 def test_list_summaries_are_not_joined(self):
  r=self.parse('<body><ul><li><p>'+A+'</p></li><li><p>'+B+'</p></li></ul></body>','legacy_body');self.assertEqual(len(r),2);self.assertFalse(r[0]['EOS'])
 def test_blocked_heading_does_not_create_end(self):
  r=self.parse('<body><p>'+A+'</p><div class="column"><h3>引用欄</h3><p>'+B+'</p></div></body>','legacy_body');self.assertEqual(len(r),1);self.assertFalse(r[0]['EOS'])
 def test_parent_introduction_is_not_section_end(self):
  r=self.parse('<body><h2>生活</h2><p>'+A+'</p><h3>買い物</h3><p>'+B+'</p></body>','legacy_body');self.assertEqual(len(r),2);self.assertFalse(r[0]['EOS'])
 def test_peer_heading_closes_original_section(self):
  r=self.parse('<body><h3>生活</h3><p>'+A+'</p><h3>買い物</h3><p>'+B+'</p></body>','legacy_body');self.assertTrue(r[0]['EOS'])
if __name__=='__main__':unittest.main()
