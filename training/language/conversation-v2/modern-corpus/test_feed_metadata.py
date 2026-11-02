import unittest
from recover_feed_metadata import metadata
class MetadataTests(unittest.TestCase):
 def test_invalid_body_does_not_change_raw(self):
  b=b'<rss><item><link>https://jp.globalvoices.org/2020/01/01/12/</link><dc:creator>A</dc:creator><content:encoded><![CDATA[<p>bad\x01body</p><div class="gv-rss-footer">Writer <a href="https://example.org/a">A</a></div>]]></content:encoded></item></rss>'
  original=bytes(b);r=metadata(b);self.assertEqual(r[0]['id'],12);self.assertEqual(r[0]['credit_links'][0]['label'],'A');self.assertEqual(b,original);self.assertNotIn('body',r[0]['public_credit_footer'])
 def test_missing_footer_not_fabricated(self):
  self.assertEqual(metadata(b'<rss><item><link>https://example.org/12/</link><content:encoded><![CDATA[body]]></content:encoded></item></rss>'),[])
 def test_non_utf8_not_repaired(self):
  with self.assertRaises(UnicodeDecodeError):metadata(b'\xff')
if __name__=='__main__':unittest.main()
