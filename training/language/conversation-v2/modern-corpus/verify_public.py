"""Validate public evidence consistency. Private source bytes require local audit."""
import json,pathlib
D=pathlib.Path(__file__).resolve().parent
FORBIDDEN={'set-cookie','cookie','authorization','proxy-authorization'}
def check(value):
 if isinstance(value,dict):
  for key,item in value.items():
   assert key.lower()not in FORBIDDEN, 'Sensitive HTTP header in public evidence'
   check(item)
 elif isinstance(value,list):
  for item in value:check(item)
def main():
 paths=[p for p in D.glob('*.json')if not p.name.startswith('FEED_')and p.name not in {'RESUME_STATUS.json','OSAKA_PILOT_ACQUISITION.json'}]
 for path in paths:check(json.loads(path.read_text()))
 census=json.loads((D/'CENSUS_TOKEN_AUDIT.json').read_text());index=json.loads((D/'CENSUS_INDEX.json').read_text());assert len(index)==census['unique_articles']==len({r['id']for r in index});assert census['admitted_body_tokens']==census['optimizer_updates']==0
 sample=json.loads((D/'CENSUS_QUALITY_PROTOCOL.json').read_text());review=json.loads((D/'CENSUS_QUALITY_REVIEW.json').read_text());assert sample['sample_size']==len(review['rows'])==review['full_sampled_paragraphs_read'];assert [r['sha256']for r in sample['selected']]==[r['sha256']for r in review['rows']]
 assert sum(census['publication_years'].values())==len(index)
 print('Public JSON, unique IDs, fixed review correspondence and Global Voices census zero-admission ledger verified. This does not describe the separately admitted STAIR research component; verify_caption_mix.py checks its selected TRAIN corpus. Private acquisition SHA/byte reconstruction not rerun by this public-only check.')
if __name__=='__main__':main()
