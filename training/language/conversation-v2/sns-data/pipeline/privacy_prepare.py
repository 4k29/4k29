"""Public-pack minimization: whole conversations/trees withheld, no edited training gold."""
import argparse,collections,gzip,hashlib,json,pathlib,shutil,re
from build import HERE,flags,sha

def main(source):
 name='oasst2-ja-original.jsonl.gz'if source=='oasst2'else'mrmpc-dialogues.jsonl.gz';p=HERE/'raw'/name
 private=pathlib.Path('/dev/shm/sns-private');private.mkdir(exist_ok=True)
 original=private/name
 if not original.exists():shutil.copyfile(p,original)
 rows=[json.loads(l)for l in gzip.open(original,'rt')];withheld=[];out=[]
 policy_path=HERE/'pipeline/publication-policy.json';policy=json.loads(policy_path.read_text());sensitive=re.compile(policy['sensitive_topic_regex'])
 if source=='oasst2':
  bad={x:{'third-party-long-translated-quotation-review'}for x in policy['manual_oasst_trees']}
  for r in rows:
   d=r['source_record'];reasons=flags(d['text'])['pii_review']
   if sensitive.search(d['text']):reasons=reasons+['sensitive-topic-public-minimization-not-personal-attribute-inference']
   if((d.get('labels')or{}).get('pii')or{}).get('value',0)>0:reasons=reasons+['source-pii-positive']
   if d.get('deleted')is not False:reasons=reasons+['deleted-or-ambiguous']
   if reasons:bad.setdefault(d['message_tree_id'],set()).update(reasons)
  for r in rows:
   d=r['source_record']
   if d['message_tree_id']in bad:
    withheld.append({'source_message_id':d['message_id'],'source_tree_id':d['message_tree_id'],'source_record_sha256':sha(json.dumps(d,ensure_ascii=False,sort_keys=True).encode()),'reasons':sorted(bad[d['message_tree_id']])})
   else:out.append(r)
  receiptpath=HERE/'raw/oasst-acquisition.json';field='japanese_subset_sha256';sizefield='japanese_subset_bytes'
 else:
  for r in rows:
   d=r['data'];reasons=sorted({x for u in d['utterances']for x in flags(u['text'])['pii_review']})
   if d['dialogue_id'] in policy['manual_mrmpc_dialogues']:reasons.append('manual-sensitive-personal-health-review')
   if any(sensitive.search(u['text'])for u in d['utterances']):reasons.append('sensitive-topic-public-minimization-not-personal-attribute-inference')
   if reasons:
    withheld.append({'source_dialogue_id':d['dialogue_id'],'source_sha256':r['sha256'],'reasons':reasons,'utterances':len(d['utterances'])})
    out.append({k:v for k,v in r.items()if k!='data'}|{'withheld':True,'withheld_reasons':reasons,'source_utterances':len(d['utterances'])})
   else:out.append(r)
  receiptpath=HERE/'raw/acquisition.json';field='archiveSha256';sizefield='archiveBytes'
 with p.open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:
   for r in out:z.write((json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 receipt=json.loads(receiptpath.read_text());receipt['pre_privacy_'+field]=sha(original.read_bytes());receipt[field]=sha(p.read_bytes());receipt[sizefield]=p.stat().st_size;receipt['public_pack_privacy_applied']=True;receipt['public_pack_records']=len(out);receipt['public_pack_withheld_records']=len(withheld)
 receiptpath.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 audit={'source':source,'publication_policy_sha256':sha(policy_path.read_bytes()),'private_quarantine_tmpfs_only':True,'unredacted_private_sha256':sha(original.read_bytes()),'public_records':len(out),'withheld_records':len(withheld),'withheld_trees':len({x['source_tree_id']for x in withheld})if source=='oasst2'else len(withheld),'withheld':withheld,'policy':'Whole source tree/dialogue withheld for contact/URL/address/source-PII, frozen sensitive-topic minimization and manual flags; intentional false positives, not a complete PII detector. No edited training text. Public pack is subset/tombstones, not original full payload.'}
 (HERE/'raw'/('privacy-'+source+'.json')).write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in audit.items()if k!='withheld'})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',choices=['mrmpc','oasst2']);main(p.parse_args().source)
