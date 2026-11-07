import pathlib,json,hashlib,urllib.request,datetime,shutil
out=pathlib.Path('/workspace/next-source-candidate-jmrd');out.mkdir(exist_ok=True)
repo=pathlib.Path('/workspace/4k29/training/language/round35/execution/next-source-not-admitted')
pin='a20b0a89b4cf6ce1db320039f6e27df10604bf4c'
url=f'https://raw.githubusercontent.com/ku-nlp/JMRD/{pin}/data/train.json'
p=out/'upstream-train.json'
if p.exists():raise SystemExit('Already acquired; inspect receipt rather than overwrite')
with urllib.request.urlopen(url,timeout=45)as response:raw=response.read()
data=json.loads(raw);assert isinstance(data,list)and len(data)==4575
p.write_bytes(raw)
for f in ['JMRD-LICENSE','JMRD-README.md','JMRD-provenance.json']:shutil.copyfile(repo/f,out/f)
info=dict(acquiredUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),repository='ku-nlp/JMRD',pinnedCommit=pin,url=url,upstreamPartition='train',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),dialogues=len(data),humanCrowdworkerOriginAsDeclaredByUpstream=True,license='CC-BY-SA-4.0',authors=['Takashi Kodama','Ribeka Tanaka','Sadao Kurohashi'],notAdmittedToAnyTraining=True,round37InputsUnchanged=True,validAndTestNotDownloaded=True,noModelOrTokenizerLoaded=True,excludedIfFutureUsed=['03042'],excludedReason='Upstream README sample already exposed',genreLimitation='Movie recommendation; not representative of all everyday conversation; grounded factual answers may require knowledge not supplied to our model',trainingCandidateFieldsOnly=['dialog[].text'],knowledgeAndCheckedKnowledgeNotPositiveTargets=True)
(out/'acquisition.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n');print(json.dumps(info))
