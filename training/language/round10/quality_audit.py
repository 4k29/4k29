"""Diagnostic only: frozen original paragraphs, never model outputs or fitting."""
import collections,hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parent

def main():
 units=json.loads((ROOT/'units.json').read_text());occ=collections.defaultdict(list)
 for u in units:
  for line in u['text'].splitlines():
   text=line.strip()
   if text:occ[text].append((u['partition'],u['site'],u['document']))
 train=[(text,rows) for text,rows in occ.items() if any(p=='train' for p,s,d in rows)]
 frequent=sorted(train,key=lambda item:sum(p=='train' for p,s,d in item[1]),reverse=True)[:50]
 rows=[dict(text=text,characters=len(text),trainOccurrences=sum(p=='train' for p,s,d in items),trainDocuments=len({d for p,s,d in items if p=='train'}),sites=sorted({s for p,s,d in items}),possibleBoilerplate=bool(re.search('PDF|ダウンロード|Adobe|お問い合わせ|関連リンク|ブラウザー|著作権',text))) for text,items in frequent]
 overlap={}
 for threshold in ['short-under80','long-at-least80']:
  selected=[(text,items) for text,items in occ.items() if (len(text)<80)==(threshold=='short-under80') and 'train' in {p for p,s,d in items} and bool({'validation','test'}&{p for p,s,d in items})]
  overlap[threshold]=dict(exactParagraphTypes=len(selected),heldOccurrences=sum(p in ['validation','test'] for text,items in selected for p,s,d in items),note='Exact trimmed paragraph overlap; counts alone do not determine evaluation leakage severity. Common short language is not quarantined by the existing >=80 grouping rule.')
 v=dict(rawUnitsSha256=hashlib.sha256((ROOT/'units.json').read_bytes()).hexdigest(),diagnosticSourceSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),diagnosticOnly=True,trainingDataChanged=False,modelOutputsUsed=False,topFrequentTrainParagraphs=rows,exactCrossPartitionParagraphOverlap=overlap)
 (ROOT/'corpus-quality-diagnostic.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(exactOverlap=overlap)))
if __name__=='__main__':main()
