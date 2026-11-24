import pathlib,urllib.request,tarfile,io,hashlib,json,datetime
P=pathlib.Path(__file__).resolve().parent;rev=json.loads((P/'asdc-tree.json').read_text())['sha'];url=f'https://codeload.github.com/megagonlabs/asdc/tar.gz/{rev}';b=urllib.request.urlopen(url,timeout=60).read();(P/'asdc-source.tar.gz').write_bytes(b);out=P/'asdc';out.mkdir(exist_ok=True);files=[]
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz')as t:
 for m in t.getmembers():
  if not m.isfile():continue
  rel=pathlib.PurePosixPath(*pathlib.PurePosixPath(m.name).parts[1:]);assert '..'not in rel.parts;data=t.extractfile(m).read();p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);files.append(dict(path=str(rel),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(P/'ACQUISITION.json').write_text(json.dumps(dict(source='megagonlabs/asdc',revision=rev,url=url,archive_bytes=len(b),archive_sha256=hashlib.sha256(b).hexdigest(),retrieved_at_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=files,corpus_license='CC-BY-4.0',program_license='Apache-2.0',attribution='Yuta Hayashibe, Accommodation Search Dialog Corpus, Megagon Labs; LREC2022 and NLP2021',original_text_modified=False),indent=2)+'\n');print('archiveMB',len(b)/1e6,'files',len(files))
