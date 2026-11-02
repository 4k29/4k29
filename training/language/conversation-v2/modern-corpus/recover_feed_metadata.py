"""Recover credit metadata from malformed RSS without repairing or training on body text.
Only item header and publisher's credit footer are inspected. All raw bytes stay unchanged.
Recovery outputs are a separate series from the strict XML collector.
"""
import pathlib,gzip,json,re,hashlib,html,xml.etree.ElementTree as ET
D=pathlib.Path(__file__).resolve().parent

def metadata(raw):
 text=raw.decode('utf-8',errors='strict');chunks=re.split(r'<item\s*>',text)[1:];result=[]
 assert len(chunks)<=10
 for chunk in chunks:
  assert '</item>'in chunk;chunk=chunk.split('</item>',1)[0];head=chunk.split('<content:encoded',1)[0]
  link=re.search(r'<link>(.*?)</link>',head,re.S);creator=re.search(r'<dc:creator>(.*?)</dc:creator>',head,re.S)
  if not link:continue
  url=html.unescape(link[1].strip());match=re.search(r'/(\d+)/?$',url)
  if not match:continue
  pos=chunk.rfind('gv-rss-footer');start=chunk.rfind('<div',0,pos)
  if pos<0 or start<0:continue
  end=chunk.find(']]>',pos)
  assert end>=0;footer=chunk[start:end];links=re.findall(r'<a[^>]+href=["\x27]([^"\x27]+)["\x27][^>]*>(.*?)</a>',footer,re.S)
  def plain(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s.replace('<![CDATA[','').replace(']]>','')))).strip()
  result.append(dict(id=int(match[1]),url=url,feed_creator=plain(creator[1])if creator else None,public_credit_footer=plain(footer),credit_links=[dict(url=html.unescape(u),label=plain(label))for u,label in links],extraction='Metadata-only literal item boundaries and original footer, no body correction'))
 return result

def main():
 targets={r['id']for r in json.loads((D/'CENSUS_INDEX.json').read_text())};records=[];fail=[]
 for path in sorted((D/'private/feed-credits').glob('*.xml.gz')):
  raw=gzip.decompress(path.read_bytes())
  try:ET.fromstring(raw);continue
  except ET.ParseError as error:problem=str(error)
  receipt=json.loads(path.with_name(path.name.replace('.xml.gz','.receipt.json')).read_text());assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
  try:
   recovered=metadata(raw)
   for row in recovered:
    if row['id']in targets:row.update(source_response_sha256=receipt['sha256'],source_feed_page=receipt['page'],strict_xml_error=problem);records.append(row)
  except (AssertionError,UnicodeDecodeError)as error:fail.append(dict(page=receipt['page'],error=str(error)))
 (D/'FEED_RECOVERED_METADATA.json').write_text(json.dumps(dict(recovered=records,unrecoverable=fail,admitted_tokens=0,optimizer_updates=0,scope='Source metadata recovery only; not prose extraction or TRAIN admission. Strict XML failure history retained.'),ensure_ascii=False,indent=2)+'\n');print('Recovered metadata records',len(records),'unrecoverable pages',len(fail))
if __name__=='__main__':main()
