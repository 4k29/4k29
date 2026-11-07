import unittest
from parse_osaka_pilot import Body
class MunicipalTests(unittest.TestCase):
 def test_scope_and_original_order(self):
  p=Body();p.feed('<nav>excluded</nav><div id="mol_contents"><h2>見出し</h2><div><p>本文&amp;原文。</p></div><p>次の段落。</p></div><footer>電話番号</footer>')
  text=''.join(p.parts);self.assertNotIn('excluded',text);self.assertNotIn('電話番号',text);self.assertIn('本文&原文。',text);self.assertLess(text.index('見出し'),text.index('次の段落'));self.assertFalse(p.active)
 def test_no_image_caption_invention(self):
  p=Body();p.feed('<div id="mol_contents"><p>原文。</p><img alt="別権利の画像説明" src="x"></div>');self.assertNotIn('別権利', ''.join(p.parts))
if __name__=='__main__':unittest.main()
