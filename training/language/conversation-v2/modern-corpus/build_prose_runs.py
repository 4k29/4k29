"""Group only consecutive already-filtered original paragraphs; never authorize EOS.
Excluded source blocks, intervening headings, and article boundaries are hard barriers.
This changes the candidate unit, not rights approval or training data.
"""
import gzip,json,pathlib,hashlib,collections,argparse
D=pathlib.Path(__file__).resolve().parent

def runs(rows):
 current=[]
 for row in rows:
  if current and (row['article_id']!=current[-1]['article_id'] or row['source_block_index']!=current[-1]['source_block_index']+1 or row['source_paragraph_index']!=current[-1]['source_paragraph_index']+1):
   yield current;current=[]
  current.append(row)
 if current:yield current

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--version',choices=['v2','v3'],default='v2');args=parser.parse_args();suffix='-v3'if args.version=='v3'else''
 stats=collections.Counter();out=D/f'private/contiguous-prose-runs{suffix}.jsonl.gz'
 with gzip.open(D/f'private/census-prose{suffix}.jsonl.gz','rt')as source,gzip.open(out,'wt')as dest:
  for group in runs(map(json.loads,source)):
   text='\n\n'.join(r['text']for r in group)
   item=dict(article_id=group[0]['article_id'],source_url=group[0]['source_url'],source_content_sha256=group[0]['source_content_sha256'],paragraph_indices=[r['source_paragraph_index']for r in group],block_indices=[r['source_block_index']for r in group],text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),processing='Original paragraph texts in source order, separated by two newlines; no bridge over omitted blocks',EOS_approved=False,admission='quarantined candidate')
   dest.write(json.dumps(item,ensure_ascii=False)+'\n');stats['runs']+=1;stats['paragraphs']+=len(group);stats['multi_paragraph_runs']+=len(group)>1;stats['characters']+=len(text)
 (D/f'CONTIGUOUS_RUN_AUDIT{suffix}.json').write_text(json.dumps(dict(counts=dict(stats),admitted_tokens=0,optimizer_updates=0,limitation='A contiguous run may still depend on preceding excluded context; no standalone completeness or rights guarantee. Artificial separation newlines are processing, not new original text.'),indent=2)+'\n')
 print(dict(stats))
if __name__=='__main__':main()
