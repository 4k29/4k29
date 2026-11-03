import unittest,hashlib
from deduplicate import deduplicate
class Duplicates(unittest.TestCase):
 def row(self,text,name):return dict(text=text,source_cache='env-r03-'+name,serial=1,text_sha256=hashlib.sha256(text.encode()).hexdigest(),body_tokens=len(text))
 def test_exact_whitespace(self):
  k,h=deduplicate([self.row('自然な文章です。次の文章です。','a'),self.row('自然な文章です。 次の文章です。','b')]);self.assertEqual(len(k),1);self.assertEqual(h[0]['reason'],'canonical_exact_unit')
 def test_same_original_paragraph(self):
  a='買い物の前に必要な品物を確認しましょう。';k,h=deduplicate([self.row(a+'\n\n'+'料理の材料を準備します。','a'),self.row(a+'\n\n'+'食品の保管には注意しましょう。','b')]);self.assertEqual(len(k),1);self.assertEqual(h[0]['reason'],'reused_original_paragraph_within_unit')
 def test_near_duplicate_long_prose(self):
  a=''.join('第'+str(i)+'の方法では、必要なものを確認してから準備を進めることが大切です。'for i in range(25));b=a.replace('準備を進める','作業を進める',1);k,h=deduplicate([self.row(a,'a'),self.row(b,'b')]);self.assertEqual(len(k),1);self.assertEqual(h[0]['reason'],'near_duplicate_character13grams')
if __name__=='__main__':unittest.main()
