"""Rebuild only a disposable new-study copy; compare SHA before removing it."""
import pathlib,json,hashlib,shutil
import build_caption_mix as builder
N=pathlib.Path(__file__).resolve().parent

def main():
 original=N/'next-foundation';scratch=N/'private/mix-rebuild-proof';assert not scratch.exists();scratch.mkdir();builder.D=scratch;builder.main();files=['MIX_POLICY.json','corpus.jsonl.gz','schedule.json.gz','DATASET_AUDIT.json'];proof=[]
 for name in files:
  a=hashlib.sha256((original/name).read_bytes()).hexdigest();b=hashlib.sha256((scratch/name).read_bytes()).hexdigest();assert a==b,name;proof.append(dict(file=name,sha256=a,bytes=(original/name).stat().st_size))
 (original/'REBUILD_PROOF.json').write_text(json.dumps(dict(all_four_byte_exact=True,files=proof,removed='Only SHA-verified disposable rebuild copy; originals, archives and Git history unchanged',optimizer_updates=0),indent=2)+'\n');shutil.rmtree(scratch);print('All4 deterministic rebuild files byte-identical; disposable copy removed',flush=True)
if __name__=='__main__':main()
