"""Conservative necessary-failure inspection aid, not a positive semantic grader.
Full unmodified outputs stay in panels/*.json. Never turns a screened item into success.
"""
import pathlib,json,collections
P=pathlib.Path(__file__).resolve().parent

def obvious_loop(tokens):
 n=len(tokens);best=None
 for start in range(n):
  for size in range(1,min(12,(n-start)//10)+1):
   unit=tokens[start:start+size];end=start+size
   while end+size<=n and tokens[end:end+size]==unit:end+=size
   reps=(end-start)//size
   if reps>=10 and end-start>=n*.5:
    candidate=dict(start=start,period_tokens=size,repetitions=reps,covered_tokens=end-start,total_tokens=n)
    if best is None or candidate['covered_tokens']>best['covered_tokens']:best=candidate
 return best

def main():
 out={}
 for name in ['A-579','B-579']:
  d=json.loads((P/'panels'/(name+'.json')).read_text());screened=[];manual=[]
  for key in ['grounded36','legacy','context12']:
   for i,r in enumerate(d[key]):
    tokens=r['nonEosTokens'];reason=None;loop=obvious_loop(tokens)
    if not r['strictUtf8']:reason='Invalid UTF8 full generated text'
    elif r['nonEosContainsSpecialTokens']:reason='Non-EOS special tokens in generated text'
    elif not(r['text']or'').strip():reason='No non-whitespace content'
    elif loop:reason='At least10 adjacent identical token periods cover at least half the complete output; obvious harmful collapse, not a semantic success'
    ident=r.get('id',str(i));base=dict(panel=r.get('panel',key),index=i,id=ident)
    if reason:screened.append(dict(**base,reason=reason,loop=loop))
    else:manual.append(dict(**base,prompt=r.get('prompt'),requirement=r.get('requirement'),program_teacher=r.get('program_teacher'),text=r['text']))
  out[name]=dict(screened_necessary_failures=screened,remaining_for_full_assistant_reading=manual,counts=dict(screened=len(screened),manual=len(manual)),screen_is_posthoc_failure_localization_not_new_adoption_standard=True,no_automatic_success=True)
 (P/'CONTENT_FAILURE_SCREEN.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v['counts']for k,v in out.items()}))
if __name__=='__main__':main()
