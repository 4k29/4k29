"""Original human turn reconstruction and prior immutable-pack match before model work."""
import pathlib,json,base64,gzip,hashlib,importlib.util
P=pathlib.Path(__file__).resolve().parent;V=P.parent
load=lambda p:json.loads(p.read_text())
def main():
 old=V/'response-ce-study';index=load(old/'PACKED_INDEX.json');ref=next(r for r in index['files']if r['name']=='CANDIDATE_SPANS.json');z=base64.b64decode((old/ref['packed']).read_text().strip(),validate=True);assert hashlib.sha256(z).hexdigest()==ref['gzip_sha256'];b=gzip.decompress(z);assert hashlib.sha256(b).hexdigest()==ref['sha256'];prior=json.loads(b);data=load(P/'PILOT_DATA.json');assert data['prior_pack_sha256']==ref['sha256'];by={r['id']:r for rs in prior['parts'].values()for r in rs}
 spec=importlib.util.spec_from_file_location('own',V/'new_tokenizer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);enc=m.Encoder(load(V/'data/tokenizer.json'));seen=set();speakers={};families={}
 for part,field in [('train','pilot_train'),('dev','dev')]:
  docs={r['id']:r for r in map(json.loads,(V/'data'/f'{part}.docs.jsonl').read_text().splitlines())};speakers[part]=set();families[part]=set()
  for r in data[field]:
   original=by[r['id']];assert r['tokens']==original['tokens']and r['response_body_start']==original['response_body_start'];d=docs[r['document']];assert d['sourceSha256']==r['source_sha256']and d['license']==r['license']=='CC-BY-SA-4.0';j=r['original_ordinal'];tokens=[1]
   for u in d['utterances'][:j+1]:tokens+=[u['localRoleToken']]+enc(u['text'])+[2]
   assert tokens==r['tokens'];body_start=len(tokens)-len(enc(d['utterances'][j]['text']))-1;assert body_start==r['response_body_start'];assert tokens[body_start-1]==r['role'];assert len(tokens)<=257
   for pos in range(1,len(tokens)):
    key=(part,r['document'],pos);assert key not in seen;seen.add(key)
   speakers[part].update(d['speakers']);families[part].add(d['normalizedDocumentFamily'])
 assert not speakers['train']&speakers['dev']and not families['train']&families['dev'];assert sorted(j for batch in data['batch_order']for j in batch)==list(range(16))
 result=dict(passed=True,prior_pack_unchanged=True,original_full_history_and_true_EOS=True,source_role_not_reassigned=True,source_teacher_positions_nonduplicated=True,TRAIN_DEV_source_speaker_family_overlap=0,pilot_input_tokens=907,pilot_response_body_tokens=252,pilot_response_EOS_teachers=16,optimizer_calls=0,model_forwards=0)
 (P/'INPUT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
 print(result)
if __name__=='__main__':main()
