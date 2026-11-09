"""Register existing exposed DEV windows in common LF1, body-only teacher mask."""
from build import *
assert not(P/'PLAN.json').exists()
source={};family={}
for path in [V/'pretraining-scale/corpus-clean.jsonl.gz',V/'foundation-stage/data.jsonl.gz']:
 for line in gzip.open(path,'rt'):
  r=json.loads(line);source[r['id']]=r['source'];family[r['id']]=r.get('family',r.get('component'))
ev=read(V/'modern-corpus/next-foundation/EVALUATION.json');rows=[]
for key in ['old_dev_windows','caption_dev','maff_dev']:
 for r in ev[key]:
  original=r['tokens'];t,keep=collapse(original);base=r['id'].rsplit('@',1)[0];base=base if base in source else base.rsplit(':',1)[0];src='stair' if key=='caption_dev' else 'maff_source_heldout' if key=='maff_dev' else 'jma' if r['panel']=='JMA' else source.get(base,'legacy_source_unresolved')
  rows.append(dict(id=r['id'],source=src,original_panel=r['panel'],tokens=t,original_tokens=original,new_to_original_position=keep,body_mask=[v>5 and v!=16 for v in t[1:]],family=family.get(base),status='Already exposed DEV diagnostic; not independent TEST'))
gzwrite(P/'DEV_BODY_NLL.json.gz',rows);print('fixed DEV groups',dict(collections.Counter(r['source'] for r in rows)))
