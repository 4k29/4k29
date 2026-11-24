"""Bundle newly added analysis only; never overwrite frozen model input/PLAN/engine."""
import pathlib,json,hashlib,gzip,tarfile,io,base64
V=pathlib.Path(__file__).resolve().parent.parent;P=V/'faq-ce-verified-study';files={}
primary=['analyze_data.py','CORPUS_AUDIT.json','SCHEDULE.json','rebuild_inputs.py','REBUILD_RECEIPT.json','numerical_contract.py','NUMERICAL_CONTRACT.json','summarize.py','SUMMARY.json','CHECKPOINT_INDEX.json','adjudicate.py','CAPTION_COMPARISON.json','CATEGORY_READING.json','verify_evidence.py','REPRODUCE.md','THIRD_PARTY_NOTICES.txt','NEXT_STRATEGY.md','REPORT.md','TABLES.md','write_report.py','prepare_publication.py']+[f'evaluation/{a}-study93-READING.json'for a in'AB']+['evaluation/initial-READING.json']
for n in primary:files[P.name+'/'+n]=(P/n).read_bytes()
for n in ['audit_adjacency.py','PAIR_ADJACENCY_AUDIT.json','audit_question_boundaries.py','QUESTION_BOUNDARY_AUDIT.json','audit_answer_strict.py','ANSWER_BOUNDARY_STRICT_AUDIT.json','prepare_clean.py','prepare_verified.py','POST_FREEZE_QUALITY.json','QUALITY_REVIEW-FINAL.json']:
 p=V/'faq-ce-study'/n
 if p.exists():files['faq-ce-study/'+n]=p.read_bytes()
for n in ['CROSS_RUN_INITIAL_CHECK.json','TOKEN_MASK_AUDIT.json','TOKENIZER_AUDIT.json','SCHEDULE.json','rebuild_inputs.py','REBUILD_RECEIPT.json']:
 p=V/'faq-ce-clean-study'/n
 if p.exists():files['faq-ce-clean-study/'+n]=p.read_bytes()
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w')as t:
 for n,b in sorted(files.items()):
  z=tarfile.TarInfo(n);z.size=len(b);z.mtime=0;t.addfile(z,io.BytesIO(b))
g=gzip.compress(buf.getvalue(),mtime=0);pack=dict(purpose='New analysis and evidence, no old input/checkpoint changes, no raw uncleared corpus',format='gzip-tar-base64',sha256=hashlib.sha256(g).hexdigest(),files={n:hashlib.sha256(b).hexdigest()for n,b in sorted(files.items())},base64=base64.b64encode(g).decode());(P/'ANALYSIS_BUNDLE.json').write_text(json.dumps(pack,separators=(',',':'))+'\n');print(len(files),'files',len(g),'compressed bytes', (P/'ANALYSIS_BUNDLE.json').stat().st_size,'pack bytes',pack['sha256'])
