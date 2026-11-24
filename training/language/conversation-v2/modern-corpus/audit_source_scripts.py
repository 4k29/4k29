"""Measure character-script composition; do not call this a language detector."""
import pathlib,json,gzip,re,collections
from acquire_pilot import Text
D=pathlib.Path(__file__).resolve().parent

def classify(text):
 out=collections.Counter();out['characters']=len(text)
 out['kana']=len(re.findall(r'[ぁ-ゖァ-ヺ]',text));out['Han']=len(re.findall(r'[一-龯㐀-䶿]',text));out['Latin_ASCII']=len(re.findall(r'[A-Za-z]',text));out['digits']=len(re.findall(r'[0-9０-９]',text));out['whitespace']=sum(c.isspace()for c in text);return out

def main():
 full=collections.Counter();filtered=collections.Counter()
 for path in sorted((D/'private/census').glob('*.json.gz')):
  for post in json.loads(gzip.decompress(path.read_bytes())):
   p=Text();p.feed(post['content']['rendered']);text='\n'.join(s.strip()for s in ''.join(p.parts).splitlines()if s.strip());full.update(classify(text))
 for line in gzip.open(D/'private/census-prose-v3.jsonl.gz','rt'):filtered.update(classify(json.loads(line)['text']))
 result=dict(full_rendered_candidate=dict(full),filtered_original_prose_candidate=dict(filtered),limitations='Character scripts are not verified language. Full articles include foreign-language quotations, translated counterparts and credits. Raw7,023,700tokens are not qualified independent Japanese TRAIN volume, nor independent meaning across translated quotations. Han may be Japanese or Chinese; Latin can occur naturally in Japanese.',admitted_tokens=0,optimizer_updates=0)
 (D/'SOURCE_SCRIPT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
