"""Remove residual website boilerplate uniformly, preserving original snapshot/SHA.
Rule motivated by VALIDATION generation, never TEST outputs. No prose repair.
"""
import collections,gzip,hashlib,json,pathlib
from collect_sources import boilerplate
ROOT=pathlib.Path(__file__).resolve().parent

def main():
    original=ROOT/'abandoned-boilerplate';original.mkdir(exist_ok=True)
    source=ROOT/'documents.jsonl';raw=source.read_bytes();docs=[json.loads(line) for line in raw.decode().splitlines()]
    with (original/'documents.jsonl.gz').open('wb') as handle:
        with gzip.GzipFile(fileobj=handle,mode='wb',mtime=0) as zipped:zipped.write(raw)
    for name in ['sources.json','split.json','generation-policy.json','tokenizer-fit-sample.json','prepare.py']:(original/name).write_bytes((ROOT/name).read_bytes())
    changed=[]
    for d in docs:
        if d['site']!='mdn':continue
        lines=d['text'].splitlines();kept=[p for p in lines if not boilerplate(p)]
        if kept==lines:continue
        old=d['textSha256'];body='\n'.join(kept);d['text']=body;d['textSha256']=hashlib.sha256(body.encode()).hexdigest();d['beforeBoilerplateTextSha256']=old
        d['blocks']=[b for b in d.get('blocks',[]) if not boilerplate(b['text'])]
        d['modifications']+=' Uniform residual browser-table/compatibility/related-section boilerplate removal; no rewritten prose.'
        changed.append(dict(id=d['id'],beforeSha256=old,afterSha256=d['textSha256'],removed=[p for p in lines if boilerplate(p)]))
    source.write_text('\n'.join(json.dumps(d,ensure_ascii=False,separators=(',',':')) for d in docs)+'\n')
    manifest=json.loads((ROOT/'sources.json').read_text());manifest['characters']=sum(len(d['text']) for d in docs);manifest['utf8Bytes']=sum(len(d['text'].encode()) for d in docs)
    manifest['sites']={s:dict(documents=sum(d['site']==s for d in docs),characters=sum(len(d['text']) for d in docs if d['site']==s)) for s in sorted({d['site'] for d in docs})}
    manifest['documentsFileSha256']=hashlib.sha256(source.read_bytes()).hexdigest();manifest['boilerplateCorrection']=dict(beforeSourceSha256=hashlib.sha256(raw).hexdigest(),reason='VALIDATION only exposed residual MDN browser compatibility boilerplate. Uniform source extraction correction, no test generation viewed.',changed=changed)
    (ROOT/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(changedDocuments=len(changed),characters=manifest['characters'],utf8Bytes=manifest['utf8Bytes'],sourceSha256=manifest['documentsFileSha256'])))
if __name__=='__main__':main()
