"""Restore only missing manifest-referenced own artifacts; never run training."""
import pathlib,json,argparse,sys
HERE=pathlib.Path(__file__).resolve().parents[1];REPO=HERE.parents[2];sys.path.insert(0,str(HERE));from checkpoint_chunks import restore,digest
p=argparse.ArgumentParser();p.add_argument('--manifest',type=pathlib.Path,default=HERE/'execution/artifact-manifest.json');p.add_argument('--check-only',action='store_true');args=p.parse_args();manifest=args.manifest.resolve();root=manifest.parent if manifest.name=='source-manifest.json'else manifest.parent.parent;record=json.loads(manifest.read_text());items=record['files']+record.get('inputs',[])+record.get('assembledCheckpoints',[]);seen=set();missing=[];restored=[]
for item in items:
 target=(root/item['path']).resolve();assert target.is_relative_to(REPO)
 if target in seen:continue
 seen.add(target)
 if target.exists():continue
 chunks=target.with_name(target.name+'.chunks.json')
 if not chunks.exists():missing.append(str(target.relative_to(REPO)));continue
 data=json.loads(chunks.read_text());assert data['sha256']==item['sha256'] and data['bytes']==item['bytes']
 if not args.check_only:
  result=restore(chunks);assert result.resolve()==target and digest(target)==item['sha256'];restored.append(str(target.relative_to(REPO)))
 else:missing.append(str(target.relative_to(REPO)))
print(json.dumps(dict(restored=restored,stillMissing=missing,checkedReferencedPaths=len(seen),optimizerUpdates=0)))
if missing:raise SystemExit(1)
