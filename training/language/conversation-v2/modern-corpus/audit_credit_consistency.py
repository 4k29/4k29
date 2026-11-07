"""Cross-check independent public publisher surfaces, without assuming human assessment."""
import pathlib,json,re,html,collections
D=pathlib.Path(__file__).resolve().parent
def norm(s):return re.sub(r'\s+','',html.unescape(s)).casefold()
def main():
 feed=json.loads((D/'FEED_ATTRIBUTIONS.json').read_text());recovered=D/'FEED_RECOVERED_METADATA.json'
 if recovered.exists():feed+=json.loads(recovered.read_text())['recovered']
 by={r['id']:r for r in feed};pages=json.loads((D/'PILOT_ATTRIBUTIONS.json').read_text());checked=[]
 for page in pages:
  if page['id']not in by:continue
  f=by[page['id']];labels={norm(x['label'])for x in f['credit_links']};authors=page['declared_original_authors'];missing=[a for a in authors if norm(a)not in labels]
  checked.append(dict(id=page['id'],original_author_names_match=not missing,missing_from_footer=missing,source_page_sha256=page['source_page_sha256'],source_feed_sha256=f['source_response_sha256']))
 output=dict(compared_public_article_and_RSS_credits=len(checked),all_original_author_names_match=all(r['original_author_names_match']for r in checked),rows=checked,current_feed_article_records=len(by),unmatched_pilot_ids=[r['id']for r in pages if r['id']not in by],limitations='Cross-surface publisher consistency, not third-party rights clearance, author verification, or independent human review. In-progress source set; rerun after acquisition.',admitted_tokens=0)
 (D/'CREDIT_CONSISTENCY.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n');print('Public page/RSS compared',len(checked),'matching',sum(r['original_author_names_match']for r in checked))
if __name__=='__main__':main()
