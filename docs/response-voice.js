// Filter authored framing, never the protected factual value supplied later.
// Answers speak directly as the profile owner rather than reporting a profile.
export function directVoicePath(path,vocabulary){
 const text=path.tokens.map(id=>vocabulary[id]).join('');
 if(path.kind==='hobbies'&&path.language==='ja'&&!/^(?:趣味は|\{value\}が趣味|楽しんでいる趣味は|趣味として楽しんでいるのは|趣味でやっているのは)/.test(text))return false;
 if(path.language==='ja'&&/(?:\{value\}が使っている|\{value\}が(?:普段の|活動の内容|執筆している内容)|\{value\}を使う製品として|普段の活動には|\{value\}への関心|アプリについては、ランニングに|靴については、ランニングに|\{value\}で呼んで)/.test(text))return false;
 // Reject accidental repeated sentence-ending particles.
 if(path.language==='ja'&&/(?:いるよ|するよ|ないよ|できるよ|読めるよ|選べるよ|開けるよ)よ/.test(text))return false;
 return !/プロフィール|登録|本人|挙げ|述べ|紹介|\bin my profile\b|\b(?:listed|registered|recorded)\b/i.test(text);
}
export function conciseAnswerPath(path,vocabulary){
 if(!directVoicePath(path,vocabulary))return false;
 if(path.language==='ja'&&/趣味の内容/.test(path.tokens.map(id=>vocabulary[id]).join('')))return false;
 if(path.kind==='audio'&&path.language==='ja')return /^(?:\{label\}は|使っている\{label\}は|普段使う\{label\}は|愛用している\{label\}は|普段の\{label\}は)/.test(path.tokens.map(id=>vocabulary[id]).join(''));
 return true;
}
// All variants keep the original protected slots and vocabulary IDs. Both
// training and browser decoding use these same complete, grammatical paths.
export function naturalGrammarPaths(paths,vocabulary){
 const result=paths.filter(p=>conciseAnswerPath(p,vocabulary)),seen=new Set();
 for(const path of [...result]){
  if(path.language!=='ja')continue;
  let tokens=[...path.tokens];
  if(path.style==='friendly'){
   if(vocabulary[tokens.at(-2)]!=='よ')continue;
   tokens.splice(-2,1);
   if(vocabulary[tokens.at(-2)]==='だ')tokens[tokens.length-2]=vocabulary.indexOf('です');
  }
  const key=path.kind+':'+tokens.join(',');if(seen.has(key))continue;seen.add(key);
  result.push({...path,id:path.id+':natural',style:'friendly',tokens});
 }
 return result.filter(path=>path.language!=='ja'||path.style!=='friendly'||vocabulary[path.tokens.at(-2)]!=='よ');
}
// Convert complete, known sentence endings rather than matching「います」
// inside unrelated conjugations such as「使います」.
export function conversationalJapanese(text){
 // Source-backed explanations already contain natural Japanese. A friendly
 // preference does not require adding「よ」to every factual sentence.
 return text;
}
