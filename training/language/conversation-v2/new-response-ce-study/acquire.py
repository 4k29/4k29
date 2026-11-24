"""Replay pinned acquisition into untracked local quarantine, never public data or model export."""
import pathlib,json,urllib.request,hashlib,datetime,concurrent.futures,argparse
P=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--quarantine-only',action='store_true',required=True,help='Local rights review only; does not authorize training or public redistribution');args=ap.parse_args()
RAW=P/'PRIVATE';RAW.mkdir(exist_ok=True);baseline=json.loads((P/'ACQUISITION.json').read_text());rows=baseline['files']
def get(row):
 row=dict(row);name=row.get('name','instruction_ja.jsonl');p=RAW/name;url=row.get('url','https://raw.githubusercontent.com/megagonlabs/instruction_ja/'+row['revision']+'/data/data.jsonl')
 b=p.read_bytes()if p.exists()else urllib.request.urlopen(url,timeout=60).read()
 if hashlib.sha256(b).hexdigest()!=row['sha256']:raise ValueError('Pinned source SHA mismatch: '+name)
 p.write_bytes(b)
 if row['source']=='ichikara-HF-mirror':
  try:r=json.loads(b);assert len(r)==row['strict_parsed_records']
  except json.JSONDecodeError:
   if row['whole_JSON_valid']:raise
 row['acquisition_url']=url;return row
acquired=list(concurrent.futures.ThreadPoolExecutor(3).map(get,rows));receipt=dict(checked_at_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=acquired,optimizer_calls=0,original_provider_form_submitted=False,personal_details_fabricated=False,quarantine_only=True)
(P/'REACQUISITION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Pinned files acquired to local quarantine:',len(acquired))
