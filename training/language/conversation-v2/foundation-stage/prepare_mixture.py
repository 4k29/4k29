"""One-factor corpus allocation control: exact active lengths/targets, no fake EOS."""
import collections,gzip,hashlib,json,pathlib
import numpy as np
from runtime import H,V,sha
def rank(s):return hashlib.sha256(('foundation-retention-v1|'+s).encode()).hexdigest()
def main():
 root=H.parents[3];meta=json.loads((V/'data/data.json').read_text());rp=root/meta['trainTokensPath'];assert sha(rp)==meta['trainTokensSha256'];values=np.fromfile(rp,dtype='<u4');windows=sorted(enumerate(meta['trainWindows']),key=lambda a:rank(str(a[0])+'|'+a[1]['document']));data=json.load(gzip.open(H/'schedule.json.gz','rt'));batches=[];pointer=0;selected=[];native_targets=rp_targets=0;counts=collections.Counter()
 for b in data['batches']:
  mixed=b[:2]
  native_targets+=sum(len(w['tokens'])-1 for w in b[:2])
  for original in b[2:]:
   length=len(original['tokens'])
   while pointer<len(windows)and windows[pointer][1]['length']<length:pointer+=1
   assert pointer<len(windows),'Do not repeat scarce conversation windows';index,w=windows[pointer];pointer+=1;s=values[w['offset']:w['offset']+length].tolist();assert 0 not in s and 5 not in s
   if 1 in s:assert w['startToken']==0 and s[0]==1 and s.count(1)==1
   target=s[1:];counts['rp_EOS_targets']+=target.count(2);counts['rp_role_targets']+=sum(t in[3,4]for t in target);counts['rp_body_targets']+=sum(t>=6 for t in target);rp_targets+=len(target)
   r=dict(id='rp:'+str(index),source_kind='original_human_A_B',tokens=s,rp_window=index,rp_offset=w['offset'],rp_length=length,document=w['document'],original_start_token=w['startToken']);mixed.append(r);selected.append(r)
  assert [len(w['tokens'])for w in b]==[len(w['tokens'])for w in mixed];batches.append(mixed)
 assert native_targets+rp_targets==data['targets'];assert len({r['rp_window']for r in selected})==len(selected)
 intervals=sorted((r['rp_offset']+1,r['rp_offset']+r['rp_length'])for r in selected);assert all(a[1]<=b[0]for a,b in zip(intervals,intervals[1:]))
 for b in batches:
  for w in b[:2]:counts['native_EOS_targets']+=w['tokens'][1:].count(2)
 payload=dict(batches=batches,dev=data['dev'],targets=data['targets'],updates=data['updates'],epochs=1,repeated_target_positions=0)
 with(H/'mixed-schedule.json.gz').open('wb')as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:z.write(json.dumps(payload,separators=(',',':')).encode())
 report=dict(changed_factor='data allocation only: two shared prose slots plus two original human dialogue replacements, per-slot valid length and every-step target budget exactly matched',source_initial='same original own3470 model/Adam/RNG; not continued from the failed pure-prose terminal',updates=data['updates'],targets=data['targets'],native_targets=native_targets,previously_seen_RP_targets=rp_targets,RP_unique_source_windows=len(selected),RP_unique_conversations=len({r['document']for r in selected}),RP_target_position_repeats=0,native_corpus_independent_volume_not_counted_twice_across_conditions=True,counts=dict(counts),native_half_coverage_inherent_to_allocation=True,role_semantics='RP remains humanA/B. No AI-self experience labels; no role ID reinterpretation in this foundation comparison.',EOS='Original human utterance EOS kept, no EOS appended at clipped RP windows. Prose boundaries unchanged.',license='Existing admitted RealPersonaChat, nu-dialogue, CC-BY-SA4.0; pinned source and split reused. No new permission or authorship claim.',schedule_sha256=sha(H/'mixed-schedule.json.gz'))
 (H/'MIXTURE_DATA_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
if __name__=='__main__':main()
