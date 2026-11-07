"""Omit only byte-verified reconstructible old encoded TRAIN working copies; retain Git objects."""
import hashlib,json,pathlib,subprocess,shutil
R=pathlib.Path(__file__).resolve().parents[4];D=pathlib.Path(__file__).resolve().parent
records=[];before=shutil.disk_usage(R).free
# Recover receipt entries from the earlier verified omissions; first attempt stopped on an untracked generated file.
for rel in subprocess.check_output(['git','ls-files'],cwd=R,text=True).splitlines():
 if rel.startswith('training/language/round') and rel.endswith('/train.tokens.bin') and not (R/rel).exists() and ('!/'+rel) in (R/'.git/info/sparse-checkout').read_text():
  b=subprocess.check_output(['git','show','HEAD:'+rel],cwd=R);records.append(dict(path=rel,git_blob=subprocess.check_output(['git','rev-parse','HEAD:'+rel],cwd=R,text=True).strip(),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),recovered_receipt_after_first_attempt=True))
for p in sorted((R/'training/language').glob('round*/**/train.tokens.bin')):
 n=p.relative_to(R/'training/language').parts[0]
 if not n[5:].isdigit() or int(n[5:]) in [25,46]:continue
 rel=str(p.relative_to(R));q=subprocess.run(['git','rev-parse','HEAD:'+rel],cwd=R,text=True,capture_output=True)
 if q.returncode:continue
 blob=q.stdout.strip();local=hashlib.sha256(p.read_bytes()).hexdigest();data=subprocess.check_output(['git','cat-file','blob',blob],cwd=R);assert hashlib.sha256(data).hexdigest()==local
 records.append(dict(path=rel,git_blob=blob,bytes=p.stat().st_size,sha256=local));subprocess.run(['git','update-index','--skip-worktree',rel],cwd=R,check=True)
 with (R/'.git/info/sparse-checkout').open('a')as f:f.write('\n!/'+rel+'\n')
 (D/'STORAGE.progress.json').write_text(json.dumps(records,indent=2)+'\n')
 p.unlink()
(D/'STORAGE.json').write_text(json.dumps(dict(before_free=before,after_free=shutil.disk_usage(R).free,files=records,git_objects_and_history_preserved=True,restore="git show HEAD:<path> > <path>; git update-index --no-skip-worktree <path>",formal_R25_R46_untouched=True),indent=2)+'\n')
print(len(records),shutil.disk_usage(R).free-before,shutil.disk_usage(R).free)
