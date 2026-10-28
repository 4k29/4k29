"""Candidate-only wider allocation schedule, not automatic semantic admission."""
import array,collections,hashlib,importlib.util,json,pathlib
H=pathlib.Path(__file__).resolve().parent;V=H.parent
R=lambda s:hashlib.sha256(('reply-wide-v1|'+str(s)).encode()).hexdigest()
def main():
 spec=importlib.util.spec_from_file_location('own',V/'new_tokenizer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);enc=m.Encoder(json.loads((V/'data/tokenizer.json').read_text()));meta=json.loads((V/'data/data.json').read_text());repo=V.parents[2];values=array.array('I');values.frombytes((repo/meta['trainTokensPath']).read_bytes());ws=meta['trainWindows'];eligible={int(k):v for k,v in json.loads((H/'eligible-windows.json').read_text()).items()};retr=json.loads((H/'RETRIEVAL.json').read_text());bad={x['id'].rsplit(':',1)[0]for x in json.loads((H/'REPLY_SAMPLE_REVIEW.json').read_text())['cases']if x['quality_hold']};eligible={i:v for i,v in eligible.items()if v['document']not in bad};bydoc=collections.defaultdict(list)
 for i,v in eligible.items():bydoc[v['document']].append(i)
 import gzip
 pairs=collections.defaultdict(list)
 for line in gzip.open(H/'retrieval-metadata.jsonl.gz','rt'):
  r=json.loads(line)
  if r['focus_proxy']and not r['common_hold']and r['document']in bydoc:pairs[r['document']].append(r)
 docmap={d['id']:d for d in map(json.loads,(V/'data/train.docs.jsonl').open())};focus={};coverage=0
 for ident,ps in pairs.items():
  d=docmap[ident];seq=[1];bounds=[]
  for u in d['utterances']:
   start=len(seq);seq +=[u['localRoleToken']]+enc(u['text'])+[2];bounds.append((start,len(seq)))
  first=next(i for i,w in enumerate(ws)if w['document']==ident);offset=ws[first]['offset']-ws[first]['startToken'];assert values[offset:offset+len(seq)].tolist()==seq
  for p in ps:
   j=p['turn']
   for i in bydoc[ident]:
    w=ws[i]
    if w['startToken']<=bounds[j-1][0]and bounds[j][1]<=w['startToken']+w['length']:
     coverage+=1;focus.setdefault(i,[]).append(p['id'])
 buckets=collections.defaultdict(list)
 for i,v in eligible.items():buckets[(ws[i]['length'],v['genre'])].append(i)
 for b in buckets.values():b.sort(key=R)
 matched=[];fd=set();cd=set();fs=collections.Counter();cs=collections.Counter()
 for i in sorted(focus,key=R):
  v=eligible[i]
  if v['document']in fd or any(fs[a]>=8 for a in v['speakers']):continue
  opts=buckets[(ws[i]['length'],v['genre'])];j=next((j for j in opts if j!=i and eligible[j]['document']not in cd and eligible[j]['document']!=v['document']and all(cs[a]<8 for a in eligible[j]['speakers'])),None)
  if j is None:continue
  matched.append((i,j));fd.add(v['document']);cd.add(eligible[j]['document']);fs.update(v['speakers']);cs.update(eligible[j]['speakers'])
  if len(matched)==512:break
 shared=[];seen=set();speakers=collections.Counter()
 for i in sorted(eligible,key=R):
  v=eligible[i]
  if v['document']in fd|cd|seen or any(speakers[a]>=8 for a in v['speakers']):continue
  shared.append(i);seen.add(v['document']);speakers.update(v['speakers'])
  if len(shared)==len(matched):break
 n=min(len(matched),len(shared));n-=n%2;matched=matched[:n];shared=shared[:n];rows=[]
 for step in range(n//2):
  f=[i for i,j in matched[step*2:step*2+2]];c=[j for i,j in matched[step*2:step*2+2]];common=shared[step*2:step*2+2];rows.append({'step':step+1,'control_window_ids':common+c,'treatment_window_ids':common+f})
 def stats(arm):
  ids=[i for r in rows for i in r[arm+'_window_ids']];seqs=[values[ws[i]['offset']+1:ws[i]['offset']+ws[i]['length']].tolist()for i in ids];flat=[x for seq in seqs for x in seq];authors=collections.Counter(a for i in ids for a in eligible[i]['speakers']);assert len(ids)==len(set(ids));return {'windows':len(ids),'unique_documents':len({ws[i]['document']for i in ids}),'unique_speakers':len(authors),'max_windows_per_speaker':max(authors.values(),default=0),'targets':len(flat),'body':sum(t>=6 for t in flat),'eos':flat.count(2),'roles':sum(t in(3,4)for t in flat),'genre_proxy':dict(collections.Counter(eligible[i]['genre']for i in ids))}
 a,b=stats('control'),stats('treatment');assert a['targets']==b['targets'];assert all([ws[i]['length']for i in r['control_window_ids']]==[ws[i]['length']for i in r['treatment_window_ids']]for r in rows)
 (H/'large-candidate-schedule.json').write_text(json.dumps({'optimizer_updates_authorized':False,'rows':rows},indent=2)+'\n');(H/'LARGE_CANDIDATE_AUDIT.json').write_text(json.dumps({'candidate_steps_per_arm':len(rows),'covered_complete_question_reply_pairs':coverage,'control':a,'treatment':b,'targets_matched':True,'coarse_genre_matched_per_replacement_slot':True,'semantic_quality_not_automatically_approved':True,'actual_optimizer_updates':0,'not_executed_reason':'Only 15/20 focus calibration examples were clean contentful, with missed privacy/factual issues; wider pool remains syntactic candidates, not fully approved response data.'},ensure_ascii=False,indent=2)+'\n');print('Candidate-only steps',len(rows),'targets',a['targets'])
if __name__=='__main__':main()
