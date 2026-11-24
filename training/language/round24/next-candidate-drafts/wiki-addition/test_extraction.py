"""Synthetic extraction fixtures only, never model training positives."""
import unittest
from collect import extract,read,R
class Tests(unittest.TestCase):
 def setUp(self):self.policy=read(R/'collection-policy.json')
 def test_original_link_prose_reference_and_template_exclusion(self):
  raw='{{Infobox|秘密の偽の文章}}\n\n水は物質です。これは自然について説明するための、日本語で書かれた十分な長さの段落です。<ref>{{Cite|title=参考資料の文章}}</ref>\n\n== 概要 ==\n\n[[水|水という物質]]は重要です。これは人が意味のつながる文章として記述した説明であり、引用や画像から読み取った文章ではありません。\n\n{{別の本文|生成してはいけない文章}}\n\n== 参考文献 ==\n\nこの参考文献の文章は採用しません。これは本文でないため、ここからの文章は入力しません。'
  blocks,reason=extract(raw,self.policy);self.assertIsNone(reason);self.assertEqual(len(blocks),3);self.assertEqual(blocks[1],'概要');self.assertIn('水という物質',blocks[2])
  for excluded in ['秘密','参考資料の文章','参考文献の文章','生成してはいけない文章']:self.assertNotIn(excluded,''.join(blocks))
  self.assertEqual(extract('{{機械翻訳}}\n\n'+raw,self.policy)[1],'machine_translation_marker')
 def test_no_formula_holes_or_empty_heading_sequence(self):
  raw='== 空見出し ==\n\n== 本文見出し ==\n\n水は重要な物質です。これは人が自然の現象について説明するために、十分な長さで記述した意味のつながる段落です。\n\n化学式<ce>H2O</ce>で示す物質は重要です。これは式を消すと対象がわからなくなるため採用しない段落です。\n\nこの現象についての説明は次の式で表される。この段落は数式のない状態では説明が完結しないため除外されます。\n\n== 末尾見出し =='
  blocks,reason=extract(raw,self.policy);self.assertIsNone(reason);self.assertEqual(len(blocks),2);self.assertEqual(blocks[0],'本文見出し');self.assertIn('水は重要',blocks[1])
if __name__=='__main__':unittest.main()
