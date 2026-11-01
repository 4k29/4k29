import unittest
from extract_prose import extract
class Boundaries(unittest.TestCase):
 def test_quotes_and_captions_never_merge_into_author_paragraph(self):
  text='自然な説明文です。'*10
  rows=extract('<p>'+text+'</p><blockquote><p>'+text+'</p></blockquote><figure><figcaption><p>'+text+'</p></figcaption></figure><p>'+text+'</p>')
  self.assertEqual([r['text']for r in rows],[text]*4);self.assertEqual([bool(r['exclusion_reasons'])for r in rows],[False,True,True,False]);self.assertEqual([r['ordinal']for r in rows],list(range(4)))
 def test_inline_caption_marks_whole_paragraph(self):
  r=extract('<p>'+('説明文です。'*12)+'<span class="caption">写真です</span></p>')[0];self.assertIn('structural_quote_caption_embed',r['exclusion_reasons'])
 def test_entities_restore_text_without_paraphrasing(self):
  text='比較は A & B です。'*8;r=extract('<p>'+text.replace('&','&amp;')+'</p>')[0];self.assertEqual(r['text'],text);self.assertFalse(r['EOS_approved'])
 def test_incomplete_paragraph_is_not_given_eos(self):
  r=extract('<p>'+('長い説明の途中です'*15))[0];self.assertIn('structural_quote_caption_embed',r['exclusion_reasons']);self.assertFalse(r['EOS_approved'])
 def test_images_do_not_poison_later_independent_paragraphs(self):
  text='段落の内容が自然につながる文章です。'*5;r=extract('<figure><img src="x"></figure><p>'+text+'</p>')[0];self.assertEqual(r['exclusion_reasons'],[])
if __name__=='__main__':unittest.main()
class Regression(unittest.TestCase):
 def test_short_attributed_quote_does_not_evade_length_proxy(self):
  r=extract('<p>'+('自然な文章です。'*8)+'彼は「映画は理解を助けます」と強調する。</p>')[0];self.assertIn('attributed_speech_or_orphan_quote_intro',r['exclusion_reasons'])
 def test_interview_speaker_is_not_silent_assistant_relabel(self):
  r=extract('<p>GV：'+('研究の経験について教えてください。'*5)+'</p>')[0];self.assertIn('interview_turn_not_prose',r['exclusion_reasons'])
 def test_removed_heading_is_an_explicit_sequence_barrier(self):
  text='自然な説明文です。'*10;r=extract('<p>'+text+'</p><h2>別の話題</h2><p>'+text+'</p>');self.assertGreater(r[1]['source_block_index']-r[0]['source_block_index'],1)
 def test_boolean_class_attribute_is_not_an_extraction_failure(self):
  text='これは日常の出来事を説明する文章です。'*6;r=extract('<p class>'+text+'</p>')[0];self.assertEqual(r['text'],text);self.assertEqual(r['exclusion_reasons'],[])
