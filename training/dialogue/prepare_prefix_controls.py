"""Reproduce corrected lineage without changing previously frozen questions.

The original controls are dated historical inputs. This only relinks their
corpus metadata; it never authors questions or fits/trains anything. The default
is a read-only reproducibility check, and --write restores the recorded files.
"""
import argparse
import copy
import hashlib
import json
import pathlib

HERE=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
read=lambda name:json.loads((HERE/name).read_text())
sha=lambda value:hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
corpus=read('prefix-corrected-corpus.json')
audit=copy.deepcopy(read('prefix-audit.json'));original=audit.pop('sourceSha256')
audit['provenance'].update(corpusSha256=corpus['sourceSha256'],originalFrozenAuditSha256=original,questionSetSha256=sha(audit['rows']),textChanges='None. Only corpus lineage metadata is relinked after correcting ambiguous training references. All100 prompts/golds remain frozen before both runs.')
audit['sourceSha256']=sha(audit)
rollouts=copy.deepcopy(read('prefix-rollouts.json'));rollouts.pop('sourceSha256')
rollouts['provenance'].update(corpusSha256=corpus['sourceSha256'],frozenAfterTrainingStart=False)
rollouts['sourceSha256']=sha(rollouts)
for name,value in [('prefix-corrected-audit.json',audit),('prefix-corrected-rollouts.json',rollouts)]:
    if args.write:(HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    else:assert value==read(name),name+' differs from the frozen historical control'
    print(name,value['sourceSha256'])
