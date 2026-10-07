"""Article links in a list must be discoverable without learning list prose."""
import pathlib,unittest
from collect import parse
ROOT=pathlib.Path(__file__).resolve().parent
class DiscoveryTests(unittest.TestCase):
 def test_bunka_cards_and_stat_sitemap_preserve_article_links(self):
  p,e=parse((ROOT/'source-policy/bunka-index.html').read_bytes());self.assertIn('/seisaku/bunkazai/index.html',p.links);self.assertIn('/seisaku/chosakuken/index.html',p.links);self.assertEqual(p.blocks,[])
  p,e=parse((ROOT/'source-policy/stat-sitemap.html').read_bytes());self.assertIn('/naruhodo/1_hajimeni/index.html',p.links);self.assertEqual(p.blocks,[])
 def test_lists_and_ruby_readings_are_excluded_from_prose(self):
  # HTML extraction fixture only; never part of model training.
  p,e=parse('<main><ul><li><a href="a.html">目次</a><p>一覧文</p></li></ul><p><ruby>統計<rt>とうけい</rt></ruby>を学ぶ。</p></main>'.encode());self.assertEqual(p.links,['a.html']);self.assertEqual([b['text'] for b in p.blocks],['統計を学ぶ。'])
if __name__=='__main__':unittest.main()
