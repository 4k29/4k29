"""Count scheduled original positions actually exposed, not the larger candidate pool."""
import pathlib,json,gzip,collections
P=pathlib.Path(__file__).resolve().parent

def main():
 corpus=[json.loads(l)for l in gzip.open(P/'corpus.jsonl.gz','rt')];schedule=json.load(gzip.open(P/'schedule.json.gz','rt'));result={}
 for arm,bs in schedule['arms'].items():
  seen=set();target=set();units=set();families=set();counts=collections.Counter()
  for batch in bs:
   for r in batch:
    row=corpus[r['record']];units.add(r['record']);families.add(row['family']);seq=row['tokens'][r['start']:r['start']+r['length']]
    for j,t in enumerate(seq,r['start']):
     if t>=6:seen.add((r['record'],j))
    for j,t in enumerate(seq[1:],r['start']+1):
     key=(r['record'],j);assert key not in target;target.add(key);counts['targets']+=1;counts['body_targets']+=t>=6;counts['EOS_targets']+=t==2
  textchars=collections.Counter()
  for i in units:textchars.update(corpus[i]['text'])
  result[arm]=dict(scheduled_units=len(units),scheduled_known_family_ids=len(families),unique_exposed_body_positions=len(seen),unique_teacher_positions=len(target),**dict(counts),source_count=len({corpus[i]['source']for i in units}),source_document_count=len({corpus[i].get('document_family',corpus[i]['family'])for i in units}),original_unit_UTF8_characters=sum(len(corpus[i]['text'])for i in units),full_units_text_digit_character_fraction=sum(n for c,n in textchars.items()if c.isdigit())/sum(textchars.values()),full_units_newline_character_fraction=textchars['\n']/sum(textchars.values()),caveat='Full-unit character statistics may include unprocessed tail of at most the hash-selected budget-truncated final reference; actual position counts above are exact.')
 out=dict(planned_exposure_not_completion=True,arms=result,no_repeated_teacher_positions=True,actual_completion_requires_receipts=True,A_unused_annotations_not_new_image_families=True,B_source_provider_is_one=True)
 (P/'EXPOSURE_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
