"""Lossless archive only already-retained immutable full states, zero updates."""
import pathlib,json,time,sys,hashlib
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from checkpoint_chunks import pack
for step in [200,1000,5000]:
 folder=R/f'execution/retained-snapshots/{step}';receipt=folder/'identity.json';raw=folder/'checkpoint.pt';manifest=folder/'checkpoint.pt.chunks.json'
 while not receipt.exists():time.sleep(20)
 expected=json.loads(receipt.read_text());assert expected['actualUpdates']==step and hashlib.sha256(raw.read_bytes()).hexdigest()==expected['checkpointSha256']
 if not manifest.exists():pack(raw)
 j=json.loads(manifest.read_text());assert j['sha256']==expected['checkpointSha256'];print('Packed actual retained full state',step,j['sha256'],flush=True)
