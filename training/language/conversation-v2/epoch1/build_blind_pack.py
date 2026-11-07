"""Package every unmodified endpoint response without disclosing endpoint identity."""
import json,pathlib,hashlib
HERE=pathlib.Path(__file__).resolve().parent

def main():
 rows=[];key={}
 for path in sorted((HERE/'evaluation').glob('*/generations.json')):
  for row in json.loads(path.read_text()):
   ident=hashlib.sha256(('epoch1-blind-v1|'+path.parent.name+'|'+row['id']).encode()).hexdigest()[:16]
   key[ident]=dict(endpoint=path.parent.name,caseId=row['id'],kind='single')
   rows.append(dict(blindId=ident,history=row['history'],sourcePrefix=row['prefixText'],unmodifiedOutput=row['text'],strictUtf8=row['strictUtf8'],rawBytesHex=row['rawBytesHex'],actualEos=row['eos'],allGeneratedTokenIds=row['tokensIncludingEos'],contentRequired=row.get('contentRequired'),minimumSemanticRequirement=row.get('minimumSemanticRequirement'),category=row.get('category')))
 for path in sorted((HERE/'evaluation').glob('*/selfplay.json')):
  for ep in json.loads(path.read_text()):
   ident=hashlib.sha256(('epoch1-blind-v1|'+path.parent.name+'|'+ep['id']).encode()).hexdigest()[:16];key[ident]=dict(endpoint=path.parent.name,caseId=ep['id'],kind='selfplay')
   rows.append(dict(blindId=ident,history=ep['originalHumanHistory'],kind='selfplay',turns=[dict(unmodifiedOutput=r['generation']['text'],strictUtf8=r['generation']['strictUtf8'],actualEos=r['generation']['eos'],tokens=r['generation']['tokensIncludingEos'])for r in ep['rows']]))
 rows.sort(key=lambda x:x['blindId']);out=HERE/'blind-pack.json';out.write_text(json.dumps(dict(scope='Independent full-output review, no model/condition labels; assistants not native human raters',rows=rows),ensure_ascii=False,indent=2)+'\n');(HERE/'blind-key.json').write_text(json.dumps(key,indent=2)+'\n');print(len(rows))
if __name__=='__main__':main()
