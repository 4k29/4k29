"""Offline reuse of fixed existing TRAIN samples; no model or optimizer objects."""
import array,collections,gzip,hashlib,importlib.util,json,os,pathlib,shutil,tempfile
H=pathlib.Path(__file__).resolve().parent;V=H.parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,d):(H/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 docs={d['id']:d for d in map(json.loads,(V/'data/train.docs.jsonl').open())};plan=json.loads((H/'PLAN.json').read_text());assert sha(V/'data/train.docs.jsonl')==plan['source_sha256']
 topics=['work','cooking','drama-travel','travel-family-health','personal-health','travel','camping','weather-preparation','game','weather-family','music','food','cooking','cooking-work','shopping','pets-family','sports','music','personal-health','game-study']
 held={2,3,4,9,15,18};notes=[]
 for i,ident in enumerate(plan['ids']):notes.append({'id':ident,'whole_dialogue_read':True,'topic':topics[i],'has_contentful_exchange':True,'status':'hold-new-export'if i in held else'conditional-human-conversation-allocation','reason':'private/sensitive context or unverified factual/health generalization; no new body publication'if i in held else'Concrete answers/follow-up/reasons observed; human experience is not AI identity or independently verified world truth'})
 write('rp-reading.json',{'source':'existingTRAIN-only','formal_human_review':False,'cases':notes,'sample_rate_not_population_estimate':True})
 spec=importlib.util.spec_from_file_location('match',V/'response-data/research/matched_schedule.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 spec=importlib.util.spec_from_file_location('enc',V/'new_tokenizer.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);enc=b.Encoder(json.loads((V/'data/tokenizer.json').read_text()))
 meta=json.loads((V/'data/data.json').read_text());p=V.parents[2]/meta['trainTokensPath'];assert sha(p)==meta['trainTokensSha256'];vals=array.array('I');vals.frombytes(p.read_bytes());ws=meta['trainWindows'];allowed={x['id']for x in notes if x['status'].startswith('conditional')};native=[]
 for i,w in enumerate(ws):
  if w['document'] not in allowed:continue
  seq=vals[w['offset']:w['offset']+w['length']].tolist();native.append({'id':str(i),'tokens':seq,'document':w['document']})
 # All native target positions unique original windows; no synthetic EOS or re-tokenization.
 controls=[(i,vals[w['offset']:w['offset']+w['length']].tolist())for i,w in enumerate(ws)]
 matched,common,skips=m.match(native,[s for _,s in controls],cap=200)
 used_replacements={k for _,k in matched}; native_ids={int(r['id'])for r,_ in matched}
 common=sorted((i for i in range(len(controls))if i not in used_replacements and i not in native_ids),key=lambda i:m.rank('rp-shared',i))[:len(matched)]
 assert len(common)==len(matched)
 schedule=[]
 for step in range(len(matched)//2):
  pair=matched[2*step:2*step+2];shared=[controls[k][0]for k in common[2*step:2*step+2]];replacement=[controls[k][0]for _,k in pair];focus=[int(r['id'])for r,_ in pair]
  schedule.append({'step':step+1,'control_window_ids':shared+replacement,'treatment_window_ids':shared+focus})
 def count(ids):return sum(ws[k]['length']-1 for k in ids)
 assert all(count(s['control_window_ids'])==count(s['treatment_window_ids'])for s in schedule)
 write('schedule.json',{'training_authorized':False,'source_tokens_sha256':sha(p),'rows':schedule})
 total=sum(count(s['control_window_ids'])for s in schedule);write('SCHEDULE_AUDIT.json',{'steps_per_arm':len(schedule),'genuine_targets_per_arm':total,'matched_per_slot':True,'focus_documents':len(allowed),'focus_windows_available':len(native),'shared_and_replacement_no_duplicate_within_arm':True,'native_source_positions_nonrepeating':True,'ordinary_full_CE_unchanged':True,'semantic_scope':'whole manually reviewed content-rich dialogue windows, not individually verified every-response labels','source_exclusion_from_control':'none: replacement pool is all existing TRAIN windows; shared half excludes chosen replacement/focus positions for no within-arm duplication','limitations':'Small conditional feasibility schedule, not all-TRAIN distribution estimate or approved semantic training data. Baseline samples all original TRAIN within target-length strata; this is not a replay of the historical shuffled sampler.','actual_optimizer_updates':0})
 # Small real fsync+atomic-replace/recovery probe; never allocate an unsafe full checkpoint.
 free=shutil.disk_usage(H).free;size=135802269
 with tempfile.TemporaryDirectory(prefix='allocation-atomic-',dir=H)as td:
  q=pathlib.Path(td);payload=os.urandom(65536)
  with (q/'next.tmp').open('wb')as f:f.write(payload);f.flush();os.fsync(f.fileno())
  os.replace(q/'next.tmp',q/'checkpoint');fd=os.open(q,os.O_RDONLY);os.fsync(fd);os.close(fd);assert(q/'checkpoint').read_bytes()==payload
 write('RESOURCE_AUDIT.json',{'free_disk_bytes_at_probe':free,'checkpoint_bytes':size,'minimum_new_terminal_plus_atomic_bytes':2*size,'initial_checkpoint_already_in_Git':True,'three_full_materialized_copies_bytes':3*size,'small_atomic_write_fsync_replace_roundtrip_passed':True,'full_checkpoint_resume_test_performed':False,'full_checkpoint_capacity_sufficient':free>=2*size,'optimizer_updates_authorized':False,'tmpfs_is_not_durable_checkpoint_storage':True,'GPU':0})
 write('SUMMARY.json',{'RP_fixed_whole_dialogues_read':20,'RP_contentful_exchange_present':20,'RP_conditional_focus_dialogues':len(allowed),'RP_new_export_holds':len(held),'steps_per_arm_proposed':len(schedule),'targets_per_arm_proposed':total,'training_go':False,'formal_adoption_go':False,'optimizer_updates':0})
if __name__=='__main__':main()
