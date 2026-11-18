"""Validate committed Git objects in a clean checkout; no optimizer steps."""
import subprocess
from experiment import *
root=P.parents[3]
for arm in 'AB':
    ledger=read(P/f'{arm}-ledger.json')
    assert len(ledger)==300
    for k in (100,300):
        folder=P/'artifacts'/f'{arm}-{k}'
        def blob(f):
            return subprocess.check_output(['git','show','HEAD:'+str(f.relative_to(root))],cwd=root)
        manifest=json.loads(blob(folder/'checkpoint.json'))
        buf=io.BytesIO()
        for part in manifest['chunks']:
            raw=blob(folder/part['path'])
            assert hashlib.sha256(raw).hexdigest()==part['sha256']
            buf.write(raw)
        assert hashlib.sha256(buf.getbuffer()).hexdigest()==manifest['sha256']
        buf.seek(0)
        st=torch.load(buf,map_location='cpu',weights_only=False)['trajectory']
        assert st['uniqueUpdates']==k and st['cursor']==k%4 and st['history']==ledger[:k]
        assert {int(s['step']) for s in st['optimizer']['state'].values()}=={k}
        print(arm,k,manifest['sha256'],digest(st),flush=True)
