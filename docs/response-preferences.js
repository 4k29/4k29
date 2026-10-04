const styles=new Set(['polite','friendly']),lengths=new Set(['brief','normal','detail']);
export function validPreferences(value){
 if(!value||typeof value!=='object')return null;
 const update={};if(styles.has(value.style))update.style=value.style;if(lengths.has(value.length))update.length=value.length;
 return Object.keys(update).length?update:null;
}
export function preferenceRequest(question){
 const text=String(question).normalize('NFKC').toLowerCase().trim();let remaining=text,update={};
 const instructions=[
  ['style','friendly',/(?:もっと|少し|ちょっと)?(?:親しみやすい|くだけた|カジュアルな|フレンドリーな)(?:口調|言葉)(?:で(?:答えて|回答して|話して|お願い(?:します)?)?)?|親しみやすい(?=[、,]|$)|(?:ため口|タメ口|敬語なし)(?:で(?:答えて|話して|お願い(?:します)?)?)?|(?:use |in )(?:a )?(?:friendly|casual) (?:tone|style)/g],
  ['style','polite',/(?:丁寧な|丁寧|ですます調の?)(?:口調|言葉)?で(?:答えて|回答して|話して|お願い(?:します)?)?|(?:use |in )(?:a )?(?:polite|formal) (?:tone|style)/g],
  ['length','brief',/(?:もっと)?(?:短く|簡潔に|手短に)(?:答えて|回答して|説明して|教えて|お願い(?:します)?)?|\b(?:keep (?:it|answers|replies) |answer |reply )?(?:briefly|brief|concise)\b(?: please)?/g],
  ['length','detail',/(?:もっと)?(?:詳しく|詳しい説明で|詳しめに)(?:答えて|回答して|説明して|教えて|お願い(?:します)?)?|(?:answer |reply |explain )in detail/g],
  ['length','normal',/(?:普通の|通常の)(?:長さ|詳しさ)で(?:答えて|お願い(?:します)?)?|(?:use |in )(?:a )?normal (?:length|detail)/g]
 ];
 const matches=[];
 for(const [key,value,pattern] of instructions)for(const match of text.matchAll(pattern)){
  // A rejected style is not an instruction to adopt that style.
  if(/^(?:は(?:なく|ない)|では(?:なく|ない)|でなく|(?:に)?(?:しない|しなく|しません)|(?:答え|話さ)ない|じゃ(?:なく|ない))/.test(text.slice(match.index+match[0].length)))continue;
  matches.push({key,value,index:match.index,text:match[0]});
 }
 matches.sort((a,b)=>a.index-b.index);for(const match of matches)update[match.key]=match.value;
 for(const match of matches.slice().reverse())remaining=remaining.slice(0,match.index)+' '+remaining.slice(match.index+match.text.length);
 remaining=remaining.replace(/^(?:これから(?:は)?|今後(?:は)?|以後(?:は)?|今回は|この回答だけ|from now on|this time|for this answer)[\s、,]*/,'').replace(/(?:してください|ください|お願いします|please)[.!。!！?？\s]*$/,'').replace(/^[\s、,.。:：]+|[\s、,.。:：!！?？]+$/g,'').trim();
 return {update:validPreferences(update),onlyInstruction:!!Object.keys(update).length&&!remaining,remaining};
}
// Only explicit requests change preferences. Generated replies and record
// frequencies are never treated as approval, preventing self-reinforcement.
export function responsePreferences(records=[],base={}){
 const result={style:'polite',length:'normal',...validPreferences(base)};
 for(const record of records.slice(-300)){
  if(record.needsReview||record.unanswered)continue;
  const request=preferenceRequest(record.question||'');
  const recorded=validPreferences(record.preferenceUpdate);
  if(recorded&&request.update)for(const [key,value] of Object.entries(recorded))if(request.update[key]===value)result[key]=value;
 }
 return result;
}
export function preferenceAcknowledgement(update,language,temporary=false){
 if(language==='en')return 'I will use '+[update.style==='friendly'?'a casual tone':update.style==='polite'?'a polite tone':'',update.length==='brief'?'shorter answers':update.length==='detail'?'more detailed answers':update.length==='normal'?'a normal answer length':''].filter(Boolean).join(' and ')+(temporary?' for this answer.':'.');
 return (temporary?'今回は、':'これからは、')+[update.style==='friendly'?'親しみやすい口調':update.style==='polite'?'丁寧な口調':'',update.length==='brief'?'短めの回答':update.length==='detail'?'詳しめの回答':update.length==='normal'?'通常の長さの回答':''].filter(Boolean).join('と')+'にします。';
}
