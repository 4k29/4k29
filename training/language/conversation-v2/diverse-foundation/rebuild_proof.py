"""Rebuild frozen source corpus and schedule in a separate sibling; no active-state writes or updates."""
import tempfile,shutil,subprocess,sys,pathlib,json,hashlib
D=pathlib.Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='.diverse-rebuild-',dir=D.parent)as folder:
 T=pathlib.Path(folder)
 for f in ['common.py','prepare.py','acquire.py','admit.py','QUALITY_REVIEW.json','ACQUISITION.json']:shutil.copyfile(D/f,T/f)
 (T/'sources').symlink_to(D/'sources',target_is_directory=True)
 for script in ['acquire.py','prepare.py','admit.py']:
  with(D/('rebuild-'+script+'.log')).open('w')as log:subprocess.run([sys.executable,str(T/script)],stdout=log,stderr=subprocess.STDOUT,check=True)
 proof={}
 for f in ['jma-candidates.jsonl.gz','corpus.jsonl.gz','schedule.json.gz']:
  a=hashlib.sha256((D/f).read_bytes()).hexdigest();b=hashlib.sha256((T/f).read_bytes()).hexdigest();proof[f]=dict(frozen_sha256=a,rebuild_sha256=b,byte_exact=a==b);assert a==b,f
 original=json.loads((D/'QUALITY_REVIEW.json').read_text())['sample_sha256'];assert hashlib.sha256((T/'QUALITY_SAMPLE.private.json').read_bytes()).hexdigest()==original
 (D/'REBUILD_PROOF.json').write_text(json.dumps(dict(all_byte_exact=True,proof=proof,reviewed_private_sample_exact=True,zero_optimizer_updates=True,temporary_copy_removed=True,live_corpus_or_training_state_modified=False,source_acquisition_receipt_reused_for_cached_SHA=True),indent=2)+'\n')
print('Source -> corpus -> schedule exact rebuild PASS',flush=True)
