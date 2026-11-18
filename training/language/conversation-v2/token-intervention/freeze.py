"""Freeze contextual top-ten choices using archived prefixes only."""
import gzip
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
V = P.parent
old = V / 'gv-collapse-diagnostic'
archive = old / 'DIAGNOSTIC.json.gz'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
rows = json.load(gzip.open(archive))['cases']
pieces = [bytes.fromhex(s) for s in json.loads((V/'data/tokenizer.json').read_text())['bytes']]
# Human inspection of prefixes and ranked tokens. 0 = no suitable candidate.
# Order is archived case order within model. First rank for onset, second for preceding position.
choices = {
'initial': [(2,2),(0,5),(0,0),(4,2),(3,2),(2,6),(0,4),(0,0),(3,2),(4,0),(2,3),(0,0)],
'B-terminal': [(3,2),(3,4),(0,0),(5,2),(2,2),(4,3),(4,2),(2,2),(3,3),(2,0),(3+1,0),(4,0),(5,2),(0,0)],
'C-terminal': [(0,2),(10,6),(3,3),(5,3),(0,0),(2,2),(2,2),(3,2),(2,2),(2,2),(3,2),(2,2),(0,0),(3,0),(2,2),(2,2),(0,2),(0,0)]}
selection = []
for row in rows:
    rep = row['repeat']
    ranks = choices[row['model']].pop(0) if rep else (0,0)
    for arm,rank in zip(('B','C'),ranks):
        j = rep['repeatStart'] - int(arm=='C') if rep else None
        entry = dict(model=row['model'],id=row['id'],arm=arm,j=j,rank=rank)
        if j is not None:
            top = row['paths']['self'][j]['top10']
            entry.update(top10=top,original=top[0][0],p_original=top[0][1])
            if rank:
                t,p = top[rank-1]
                word = pieces[t].decode('utf8')
                assert t > 5 and word.strip() and t != top[0][0]
                entry.update(token=t,p=p,piece=word)
        selection.append(entry)
assert not any(choices.values())
plan = dict(models=json.loads((old/'PLAN.json').read_text())['models'],archive_SHA=digest(archive),
    inputs_SHA=digest(V/'gv-prose-pilot/EVALUATION_INPUTS.json'), selection=selection,
    rule='Rank table from inspection of local baseline history and archived top10 only. Prefer locally attachable grammatical or topic-compatible pieces, abstain for arbitrary names/digits or broken stems. No oracle or retries. Local fit is nonblind and judgmental.',
    control='Repeat onset minus one. May share earlier disfluency; not an untreated random sample. No target on nonrepeat trajectories.',
    primary='Only autonomous suffix after replacement counts. Two complete new coherent topical sentences, natural through stop, no harmful repetition or paraphrase loop. No minimum beyond two sentences. EOS scored independently. Common original total budget 128 tokens including forced token. Never extend after EOS.',
    recurrence='Earliest four-gram starting strictly after replacement with prior occurrence anywhere in generated continuation. Distance in zero-based token positions. Mechanical recurrence separately from semantic harm.')
(P/'PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=1)+'\n')
(P/'PLAN.sha256').write_text(digest(P/'PLAN.json')+'\n')
