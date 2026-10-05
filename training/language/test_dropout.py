"""Stochastic own BPE must preserve raw bytes and canonical behavior."""
import json,pathlib,random,sys,unittest
from prepare_paragraphs import encode_dropout,usable_paragraph
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'dialogue'))
from tokenizer import encode_stream
class DropoutTests(unittest.TestCase):
 def setUp(self):self.tok=json.loads((pathlib.Path(__file__).resolve().parent/'bpe-4096/tokenizer.json').read_text())
 def test_zero_dropout_is_canonical_and_stochastic_views_preserve_original_bytes(self):
  for text in ['どちらのリストを使用するか判断するには、順序を変更してみてください。','parseInt は2つの引数を受け取ります。','またその青宝玉の尖った粒をきれいに並べました。','Nothing Headphone (1)はヘッドホンです。','「この文章には、ことばと記号が含まれています。」']:
   self.assertEqual(encode_dropout(text,self.tok,random.Random(729),0),encode_stream(text,self.tok))
   for p in [.15,.3,1]:
    a=encode_dropout(text,self.tok,random.Random(729),p);b=encode_dropout(text,self.tok,random.Random(729),p);self.assertEqual(a,b);self.assertEqual(b''.join(bytes.fromhex(self.tok['bytes'][t]) for t in a),text.encode())
   self.assertEqual(encode_dropout(text,self.tok,random.Random(729),1),[c+6 for c in text.encode()])
 def test_complete_prose_is_retained_but_layout_and_contact_fragments_are_rejected(self):
  self.assertTrue(usable_paragraph('これは実際の日本語の説明文で、何かの使い方や言葉の意味を、最後まで通る自然な文章で説明しています。'))
  for p in ['一','構文','参考資料','消費者の部屋への相談電話は03-5512-1115です。'+'詳細なお問い合わせについては参考資料をご覧ください。','これは長い説明文ですが、最後まで文章として閉じずに、ある単語の途中で終わってしま']:
   self.assertFalse(usable_paragraph(p))
if __name__=='__main__':unittest.main()
