"""Conservative necessary-failure screening; all other cases require full main-assistant reading."""
import pathlib,json,hashlib,sys
P=pathlib.Path(__file__).resolve().parent;V=P.parent
pieces=[bytes.fromhex(x) for x in json.loads((V/'data/tokenizer.json').read_text())['bytes']]
def obvious_loop(t):
 best=0
 for period in range(1,13):
  for start in range(len(t)):
   end=start+period
   while end+period<=len(t) and t[end:end+period]==t[start:start+period]:end+=period
   n=(end-start)//period
   if n>=10:best=max(best,end-start)
 return best>=len(t)*.5 and best>0
name=sys.argv[1];x=json.loads((P/'evaluation'/(name+'.json')).read_text());cards=[];screen=[]
for c in x['cases']:
 pre=b''.join(pieces[t] for t in c['prefix'] if t>5).decode('utf8','backslashreplace');auto=obvious_loop(c['nonEosTokens']);r=dict(id=c['id'],panel=c['panel'],necessary_failure=auto,method='same prior conservative screen: >=10 adjacent periods occupy >=half of full output' if auto else 'full-text main-assistant review required',semantic_success=False if auto else None)
 screen.append(r)
 if not auto:cards.append(dict(id=c['id'],panel=c['panel'],prefix=pre,prompt=c.get('prompt'),requirement=c.get('requirement'),generation=c['text'],EOS=c['eos'],rawBytesHex=c['rawBytesHex']))
(P/'evaluation'/(name+'-SCREEN.json')).write_text(json.dumps(screen,ensure_ascii=False,indent=2)+'\n');(P/'evaluation'/(name+'-REVIEW_CARDS.json')).write_text(json.dumps(cards,ensure_ascii=False,indent=2)+'\n');print(name,'necessary failures',sum(c['necessary_failure'] for c in screen),'manual',len(cards))
for c in cards:print(json.dumps(c,ensure_ascii=False))
