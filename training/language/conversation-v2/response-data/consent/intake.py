"""Offline consent intake. No real providers, signature verification or training implied."""
import argparse, hashlib, json, pathlib, re
GRANTS = ('acquisition','storage','processing','model_training')

def digest(x):
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def validate(d, public=False):
    errors=[]
    if d.get('schema_version') != 1 or d.get('consent_version') != 'response-consent-v1':
        errors.append('unsupported-contract')
    if not d.get('submission_id'):
        errors.append('missing-submission-id')
    participants=d.get('participants',[]); ids=[p.get('id') for p in participants]
    if len(ids)<2 or None in ids or len(ids)!=len(set(ids)):
        errors.append('need-distinct-consenting-participants')
    for p in participants:
        if not re.fullmatch(r'[0-9a-f]{64}',p.get('private_evidence_sha256','')):
            errors.append('missing-private-consent-evidence-digest')
        if any(p.get('grants',{}).get(k) is not True for k in GRANTS):
            errors.append('required-grant-not-explicit')
        if p.get('withdrawal_terms_acknowledged') is not True:
            errors.append('withdrawal-terms-not-acknowledged')
        if p.get('owns_submitted_utterances') is not True:
            errors.append('ownership-unconfirmed')
        if public and (p.get('grants',{}).get('public_redistribution') is not True
                       or p.get('dataset_license')!='CC-BY-SA-4.0'):
            errors.append('public-license-not-granted-by-every-author')
    review=d.get('review',{})
    if review.get('status')!='approved' or not review.get('reviewer') or review.get('evidence_manually_checked') is not True:
        errors.append('actual-consent-evidence-needs-manual-review')
    messages=d.get('messages',[]); seen=set(); authors=set()
    for i,m in enumerate(messages):
        if not m.get('id') or m['id'] in seen: errors.append('invalid-message-identity')
        if m.get('author') not in ids: errors.append('author-consent-missing')
        if m.get('parent_id') is not None and m['parent_id'] not in seen: errors.append('missing-or-future-parent')
        if i and m.get('parent_id') is None: errors.append('multiple-roots-not-single-conversation')
        text=m.get('text','')
        if not isinstance(text,str) or not text: errors.append('missing-original-text')
        elif re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\d)0\d{1,3}[- ]\d{2,4}[- ]\d{3,4}(?!\d)',text):
            errors.append('contact-information-needs-private-review')
        if m.get('third_party_material_cleared') is not True:
            errors.append('third-party-material-not-cleared')
        seen.add(m.get('id')); authors.add(m.get('author'))
    if len(messages)<2 or len(authors)<2: errors.append('not-multi-person-conversation')
    return sorted(set(errors))

def intake(documents, public=False):
    accepted=[]; reports=[]; seen=set()
    for d in documents:
        errors=validate(d,public)
        ident=d.get('submission_id')
        if ident in seen: errors.append('duplicate-submission')
        seen.add(ident)
        reports.append({'submission_digest':digest(d),'eligible_for_candidate_processing':not errors,'reasons':errors})
        if not errors:
            accepted.append({'source':'direct-consent','id':ident,'rights_status':'consent-reviewed-quality-pending',
                             'training_admitted':False,'public_redistribution':public,
                             'messages':d['messages'], 'participants':[p['id'] for p in d['participants']],
                             'consent_record_digest':digest(d)})
    return accepted, {'submissions_received':len(documents),'candidate_submissions':len(accepted),
                      'training_admitted':0,'optimizer_updates':0,'reports':reports,
                      'limitations':['local reviewer attestation is not cryptographic identity/signature proof',
                                     'regex cannot certify privacy or authorship; manual source review remains required']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('private_input_directory',type=pathlib.Path)
    p.add_argument('output_directory',type=pathlib.Path);p.add_argument('--public',action='store_true');a=p.parse_args()
    if not a.private_input_directory.is_dir():p.error('Input directory must exist; never invent submissions')
    docs=[json.loads(f.read_text()) for f in sorted(a.private_input_directory.glob('*.json'))]
    records,receipt=intake(docs,a.public);a.output_directory.mkdir(parents=True,exist_ok=True)
    (a.output_directory/'candidates.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in records))
    (a.output_directory/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='reports'},ensure_ascii=False))
if __name__=='__main__':main()
