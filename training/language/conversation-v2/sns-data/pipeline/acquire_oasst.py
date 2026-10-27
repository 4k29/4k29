"""Official Apache2 source; acquire original ja rows, never translate or use synthetic rows."""
import datetime,gzip,hashlib,json,pathlib,urllib.request
HERE=pathlib.Path(__file__).resolve().parents[1]
REV='179dd21fc55192153d94adb0e0ce8f69e222bf75';NAME='2023-11-05_oasst2_ready.messages.jsonl.gz'
URL='https://huggingface.co/datasets/OpenAssistant/oasst2/resolve/'+REV+'/'+NAME

def main():
 readme=urllib.request.urlopen('https://huggingface.co/datasets/OpenAssistant/oasst2/resolve/'+REV+'/README.md',timeout=60).read();assert b'apache-2.0'in readme
 (HERE/'raw/OASST2-README.md').write_bytes(readme)
 path=pathlib.Path('/dev/shm/oasst2-ready.messages.jsonl.gz');h=hashlib.sha256();total=0
 with urllib.request.urlopen(URL,timeout=120)as r,path.open('wb')as f:
  while True:
   b=r.read(1048576)
   if not b:break
   total+=len(b)
   if total>60000000:raise ValueError('source budget exceeded')
   h.update(b);f.write(b)
 assert total==54301900
 selected=[];counts={};reasons={};totalrows=0
 for line in gzip.open(path,'rt'):
  d=json.loads(line);totalrows+=1
  if d['lang']!='ja':continue
  reason=[]
  if d.get('synthetic')is not False:reason.append('synthetic-not-explicitly-false')
  if d.get('model_name'):reason.append('model-name-present')
  if d.get('deleted')is not False:reason.append('deleted-not-explicitly-false')
  if d.get('review_result')is not True:reason.append('review-not-explicitly-true')
  for x in reason:reasons[x]=reasons.get(x,0)+1
  # Source-local pseudonyms and privacy annotations retained. Original JA subset only.
  if d.get('deleted') is not False:
   d=dict(d);d['text']='';d['text_withheld']='deleted-or-ambiguous-deletion'
  selected.append({'source_record':d,'eligibility_flags':reason})
 out=HERE/'raw/oasst2-ja-original.jsonl.gz'
 with out.open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:
   for row in selected:z.write((json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 receipt={'source':'oasst2','revision':REV,'source_url':URL,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'license':'Apache-2.0','source_compressed_bytes':total,'source_compressed_sha256':h.hexdigest(),'total_source_rows_streamed':totalrows,'original_japanese_rows':len(selected),'ineligible_flags':reasons,'japanese_subset_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'japanese_subset_bytes':out.stat().st_size,'non_japanese_content_retained':False,'source_annotation_not_human_authorship_proof':True,'synthetic_or_ambiguous_never_eligible':True,'original_upstream_train_validation_not_preserved':'ready source has no original split column; new component split required, no sealedTEST'}
 (HERE/'raw/oasst-acquisition.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
if __name__=='__main__':main()
