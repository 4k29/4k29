"""Inspect raw-source distribution, repetition/overlap and source attribution."""
import collections,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent

def main():
 docs=[json.loads(s) for s in (ROOT/'documents.jsonl').read_text().splitlines()];split=json.loads((ROOT/'split.json').read_text());parts={r['document']:r['partition'] for r in split['assignments']};paragraphs=collections.defaultdict(list)
 for d in docs:
  for p in set(d['text'].splitlines()):
   if len(p)>=80:paragraphs[p].append(d['id'])
 overlaps=[dict(paragraphSha256=hashlib.sha256(p.encode()).hexdigest(),characters=len(p),documents=ids,partitions=sorted({parts[i] for i in ids})) for p,ids in paragraphs.items() if len({parts[i] for i in ids})>1]
 counts={s:{part:dict(documents=sum(d['site']==s and parts[d['id']]==part for d in docs),characters=sum(len(d['text']) for d in docs if d['site']==s and parts[d['id']]==part)) for part in ['train','validation','test']} for s in sorted({d['site'] for d in docs})}
 credits=[]
 for d in docs:
  attribution=d.get('attribution') or ('MDN contributors: '+d['title']+' ('+d['url']+') を加工して作成' if d['site']=='mdn' else '出典：'+d['author']+'ホームページ（'+d['url']+'）を加工して作成' if d['site']!='aozora' else d['author']+'「'+d['title']+'」青空文庫 ('+d['url']+')')
  credits.append(dict(document=d['id'],author=d['author'],title=d['title'],url=d['url'],license=d['license'],licenseUrl=d['licenseUrl'],attribution=attribution,modifications=d['modifications'],**({'bibliography':d['bibliography']} if d['site']=='aozora' else {})))
 (ROOT/'source-credits.json').write_text(json.dumps(credits,ensure_ascii=False,indent=2)+'\n')
 report=dict(sourceSha256=hashlib.sha256((ROOT/'documents.jsonl').read_bytes()).hexdigest(),characters=sum(len(d['text']) for d in docs),utf8Bytes=sum(len(d['text'].encode()) for d in docs),distribution=counts,longExactParagraphsSharedAcrossPartitions=overlaps,note='Entire document groups are disjoint. Vocabulary/weights fit TRAIN only. Short common phrases naturally overlap. Remaining isolated exact paragraphs are disclosed here; validation likelihood is not evidence that every held phrase is novel. Source prose style is mostly older literary Japanese; modern orthography does not guarantee contemporary conversational tone. TEST raw openings are separately verified absent from all TRAIN bodies.')
 (ROOT/'data-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(characters=report['characters'],crossPartitionLongParagraphs=len(overlaps),distribution=counts)))
if __name__=='__main__':main()
