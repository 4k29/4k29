"""Recompute the frozen TRAIN-only predicate and verify all-view unit membership."""
import pathlib,json,re,collections,hashlib
R=pathlib.Path(__file__).resolve().parents[1];read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=read(R/'training-unit-selection.json');assert sha(R/'training-unit-selection.json')==read(R/'policy.json')['trainingSelectionSha256']
u=[x for x in read(R.parent/'round10/units.json') if x['partition']=='train'];decisions=[];selected=[];counts=collections.defaultdict(collections.Counter)
for x in u:
 t=x['text'];assert hashlib.sha256(t.encode()).hexdigest()==x['textSha256']
 eligible=x['site']=='aozora' or (len(re.findall('[。！？]',t))>=2 and t.rstrip().rstrip('」』）)"').endswith(('。','！','？')) and len(re.findall('[ぁ-ゖァ-ヺ一-龯]',t))/max(1,len(t))>=.5)
 key=x['document']+':chain:'+str(x['startLine']);counts[x['site']]['total']+=1;counts[x['site']]['selected']+=int(eligible)
 if eligible:selected.append(key)
 decisions.append(dict(unit=key,textSha256=x['textSha256'],site=x['site'],selected=eligible))
assert selected==s['selectedUnits'] and decisions==s['decisions'] and {k:dict(v) for k,v in counts.items()}==s['siteCounts']
i=read(R.parent/'round11/multiview/train.index.json');allowed=set(selected);views=collections.defaultdict(set)
for row in i['rows']:
 key=row['unit'].rsplit(':view:',1)[0]
 if key in allowed:views[key].add(row['variant'])
assert set(views)==allowed and all(v=={0,1,2} for v in views.values())
record=dict(selectedTrainUnits=len(selected),excludedTrainUnits=len(u)-len(selected),allRetainedUnitsPresentInAllThreeViews=True,rawTextHashesVerified=True,selectionPredicateExactlyReproduced=True,additionalOptimizerUpdates=0,selectionSha256=sha(R/'training-unit-selection.json'))
(R/'execution/selection-integrity.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
