"""Bounded primary-source terms/metadata fetch; never fetches SNS posts."""
import urllib.request, urllib.error, hashlib, json, datetime, pathlib, re, html
ROOT=pathlib.Path(__file__).resolve().parent
SOURCES={
'bluesky_terms':'https://bsky.social/about/support/tos',
'bluesky_developer':'https://bsky.social/about/support/developer-guidelines',
'bluesky_rate':'https://docs.bsky.app/docs/advanced-guides/rate-limits',
'bluesky_threads':'https://docs.bsky.app/docs/api/app-bsky-feed-get-post-thread',
'mastodon_api':'https://docs.joinmastodon.org/methods/timelines/',
'mastodon_context':'https://docs.joinmastodon.org/methods/statuses/',
'mastodon_rate':'https://docs.joinmastodon.org/api/rate-limits/',
'mastodon_social_terms':'https://mastodon.social/terms',
'misskey_api':'https://misskey-hub.net/en/docs/for-developers/api/',
'misskey_io_terms':'https://misskey.io/terms',
'misskey_io_privacy':'https://misskey.io/privacy-policy',
'x_policy':'https://developer.x.com/en/developer-terms/agreement-and-policy',
'x_agreement':'https://developer.x.com/en/developer-terms/agreement',
'reddit_data':'https://redditinc.com/policies/data-api-terms',
'reddit_user':'https://redditinc.com/policies/user-agreement',
'nucc':'https://mmsrv.ninjal.ac.jp/nucc/',
'jed':'https://github.com/imai-laboratory/EmpatheticDialoguesCorpus',
'cc4':'https://creativecommons.org/licenses/by-sa/4.0/legalcode.en',
}
SOURCES.update({'bluesky_developer_source': 'https://raw.githubusercontent.com/bluesky-social/bsky-docs/main/docs/support/developer-guidelines.md', 'bluesky_rate_source': 'https://raw.githubusercontent.com/bluesky-social/bsky-docs/main/docs/advanced-guides/rate-limits.md', 'mastodon_instance_terms_api': 'https://mastodon.social/api/v1/instance', 'nucc_download': 'https://mmsrv.ninjal.ac.jp/nucc/nucc.html', 'misskey_io_rules': 'https://go.misskey.io/terms-of-service', 'misskey_io_privacy_link': 'https://go.misskey.io/privacy-policy', 'nu-dialogue-jmultiwoz-README.md': 'https://raw.githubusercontent.com/nu-dialogue/jmultiwoz/a78dd334b907e12318b76bb23d0a9ed1498b8d15/README.md', 'nu-dialogue-jmultiwoz-LICENSE': 'https://raw.githubusercontent.com/nu-dialogue/jmultiwoz/a78dd334b907e12318b76bb23d0a9ed1498b8d15/LICENSE', 'nu-dialogue-jmultiwoz-dataset-README.md': 'https://raw.githubusercontent.com/nu-dialogue/jmultiwoz/a78dd334b907e12318b76bb23d0a9ed1498b8d15/dataset/README.md', 'nu-dialogue-multi-relational-multi-party-chat-corpus-README.md': 'https://raw.githubusercontent.com/nu-dialogue/multi-relational-multi-party-chat-corpus/e6e39cb896df88781c7a2e0451226a527c5f1e2e/README.md', 'nu-dialogue-multi-relational-multi-party-chat-corpus-LICENSE': 'https://raw.githubusercontent.com/nu-dialogue/multi-relational-multi-party-chat-corpus/e6e39cb896df88781c7a2e0451226a527c5f1e2e/LICENSE', 'ku-nlp-JMRD-README.md': 'https://raw.githubusercontent.com/ku-nlp/JMRD/a20b0a89b4cf6ce1db320039f6e27df10604bf4c/README.md', 'ku-nlp-JMRD-LICENSE': 'https://raw.githubusercontent.com/ku-nlp/JMRD/a20b0a89b4cf6ce1db320039f6e27df10604bf4c/LICENSE', 'jqk09a-japanese-daily-dialogue-README.md': 'https://raw.githubusercontent.com/jqk09a/japanese-daily-dialogue/5e612e02da1228e22d2c8eec6aebe6eaa15b48f9/README.md', 'OpenAssistant-oasst1-README.md': 'https://huggingface.co/datasets/OpenAssistant/oasst1/raw/fdf72ae0827c1cda404aff25b6603abec9e3399b/README.md', 'OpenAssistant-oasst2-README.md': 'https://huggingface.co/datasets/OpenAssistant/oasst2/raw/179dd21fc55192153d94adb0e0ce8f69e222bf75/README.md', 'kunishou-oasst2-135k-ja-README.md': 'https://huggingface.co/datasets/kunishou/oasst2-135k-ja/raw/af218f0f269812551436c1b659ab8089ca20286a/README.md', 'bluesky-social-atproto-post.json': 'https://raw.githubusercontent.com/bluesky-social/atproto/66ce7c5fde851be67c0b36362ef75ea3b0a46df6/lexicons/app/bsky/feed/post.json', 'bluesky-social-atproto-getPostThread.json': 'https://raw.githubusercontent.com/bluesky-social/atproto/66ce7c5fde851be67c0b36362ef75ea3b0a46df6/lexicons/app/bsky/feed/getPostThread.json', 'misskey-dev-misskey-children.ts': 'https://raw.githubusercontent.com/misskey-dev/misskey/d9b1fc50ad4d57f708b9d6bc6fa7a763bb18602f/packages/backend/src/server/api/endpoints/notes/children.ts', 'misskey-dev-misskey-conversation.ts': 'https://raw.githubusercontent.com/misskey-dev/misskey/d9b1fc50ad4d57f708b9d6bc6fa7a763bb18602f/packages/backend/src/server/api/endpoints/notes/conversation.ts', 'misskey-dev-misskey-search.ts': 'https://raw.githubusercontent.com/misskey-dev/misskey/d9b1fc50ad4d57f708b9d6bc6fa7a763bb18602f/packages/backend/src/server/api/endpoints/notes/search.ts'})
SOURCES.update({'OpenAssistant-upstream-LICENSE': 'https://raw.githubusercontent.com/LAION-AI/Open-Assistant/f1e6ed9526f5817531f3ab85441a40b3671ddccb/LICENSE', 'OpenAssistant-upstream-terms-of-service.tsx': 'https://raw.githubusercontent.com/LAION-AI/Open-Assistant/f1e6ed9526f5817531f3ab85441a40b3671ddccb/website/src/pages/terms-of-service.tsx', 'OpenAssistant-upstream-privacy-policy.tsx': 'https://raw.githubusercontent.com/LAION-AI/Open-Assistant/f1e6ed9526f5817531f3ab85441a40b3671ddccb/website/src/pages/privacy-policy.tsx'})
SOURCES.update({'OpenAssistant-upstream-ToS.tsx': 'https://raw.githubusercontent.com/LAION-AI/Open-Assistant/f1e6ed9526f5817531f3ab85441a40b3671ddccb/website/src/components/ToS.tsx'})
def main():
 out=[]; (ROOT/'evidence').mkdir(exist_ok=True)
 for name,url in SOURCES.items():
  rec={'id':name,'url':url,'checkedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'4k29-conversation-research/1.0 (terms audit; no post collection)'})
   with urllib.request.urlopen(req,timeout=30) as r:
    b=r.read(2_000_001)
    if len(b)>2_000_000: raise ValueError('2MB evidence budget exceeded')
    rec.update(http=r.status,finalUrl=r.url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    # Preserve primary evidence as bounded html/text, not a claim of current forever.
    p=ROOT/'evidence'/f'{name}.html'; p.write_bytes(b); rec['snapshot']=str(p.relative_to(ROOT))
    t=b.decode('utf8',errors='replace'); t=re.sub(r'<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>','',t,flags=re.S|re.I);t=html.unescape(re.sub('<[^>]+>',' ',t));t=re.sub(r'\s+',' ',t)
    (ROOT/'evidence'/f'{name}.txt').write_text(t)
  except Exception as e:rec.update(error=str(e),http=getattr(e,'code',None))
  out.append(rec); print(name,rec.get('http'),rec.get('bytes'),rec.get('error',''))
 (ROOT/'fetch-receipt.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
