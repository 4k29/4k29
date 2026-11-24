import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import unittest,pathlib,json,tempfile,hashlib
from prefix_selection import HumanTurnPrefixSelector,load_selector
class PrefixPolicyTests(unittest.TestCase):
 def setUp(self):
  self.tok={'bytes':['']*6+['61','80','e3','0a']};self.info={'documents':[{'id':'u','site':'human-chat','length':200}]};self.feature={'boundariesByUnit':{'u':[5,12,25,32,40,125]}};self.selector=HumanTurnPrefixSelector(self.feature,self.tok,self.info)
 def row(self,**kw):return dict({'site':'human-chat','unit':'u','start':0,'length':100},**kw)
 def test_existing_exact_end_keeps_full_budget(self):self.assertEqual(self.selector.length(self.row(),1),32)
 def test_latest_visible_end_and_relative_window_offsets(self):
  self.assertEqual(self.selector.length(self.row(length=31),1),25);self.assertEqual(self.selector.length(self.row(start=100),6),25)
 def test_minimum_context_and_short_row_fallback(self):
  self.assertEqual(self.selector.length(self.row(length=11),1),10);self.assertEqual(self.selector.length(self.row(length=5),1),4)
 def test_never_truncates_other_genres_or_reads_their_map(self):self.assertEqual(self.selector.length(self.row(site='aozora',unit='other'),6),32)
 def test_byte_continuation_start_falls_back_and_leading_byte_is_valid_start(self):
  self.assertEqual(self.selector.length(self.row(length=31),7),30);self.assertEqual(self.selector.length(self.row(length=31),8),25)
 def test_padding_or_other_empty_special_cannot_enable_new_cut(self):self.assertEqual(self.selector.length(self.row(length=31),0),30)
 def test_missing_source_and_interior_bos_rejected(self):
  with self.assertRaises(ValueError):self.selector.length(self.row(unit='unknown'),1)
  with self.assertRaises(ValueError):self.selector.length(self.row(start=100),1)
 def test_unsorted_or_out_of_bounds_map_rejected(self):
  for ends in [[25,12],[12,12],[200],[0]]:
   with self.assertRaises(ValueError):HumanTurnPrefixSelector({'boundariesByUnit':{'u':ends}},self.tok,self.info)
if __name__=='__main__':unittest.main()
