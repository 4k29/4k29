"""Independently verify every cached source dialogue against pinned Git blob identity."""
import hashlib,json,pathlib,urllib.request
from acquire_mrmpc import HERE,REPO,REV
u='https://api.github.com/repos/'+REPO+'/git/trees/'+REV+'?recursive=1'
tree=json.load(urllib.request.urlopen(u,timeout=45));rows=[]
for x in tree['tree']:
 if not(x['type']=='blob'and x['path'].startswith('multi_relational_multi_party_chat_corpus/dialogues/')and x['path'].endswith('.json')):continue
 p=pathlib.Path('/dev/shm/sns-mrmpc')/pathlib.Path(x['path']).name;b=p.read_bytes();actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert actual==x['sha']and len(b)==x['size']
 rows.append({'path':x['path'],'git_blob_sha1':actual,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
assert len(rows)==960
(HERE/'raw/git-source-verification.json').write_text(json.dumps({'passed':True,'revision':REV,'metadata_url':u,'dialogues':len(rows),'metadata_not_source_profile_acquired':True,'rows':rows},indent=2)+'\n')
print('960 pinned Git blob identities verified')
