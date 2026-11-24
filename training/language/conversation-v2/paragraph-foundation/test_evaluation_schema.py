import unittest
from evaluation_schema import combine_case
class Schema(unittest.TestCase):
 def test_source_and_generated_full_text_are_both_retained(self):
  source=dict(id='x',text='原文です。',prefix=[1,10]);g=dict(text='生成文です。',tokensIncludingEos=[11,2],rawBytesHex='abcd')
  result=combine_case(source,g);self.assertEqual(result['source_reference_text'],'原文です。');self.assertEqual(result['text'],'生成文です。');self.assertEqual(result['rawBytesHex'],'abcd');self.assertEqual(source['text'],'原文です。')
 def test_unexpected_collision_is_not_silently_overwritten(self):
  with self.assertRaises(ValueError):combine_case(dict(id='x',eos=False),dict(eos=True))
if __name__=='__main__':unittest.main()
