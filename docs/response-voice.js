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
// Convert complete, known sentence endings rather than matching「います」
// inside unrelated conjugations such as「使います」.
export function conversationalJapanese(text){
 const endings=[['ていません','ていないよ'],['でいません','でいないよ'],['ています','ているよ'],['でいます','でいるよ'],['できます','できるよ'],['使います','使うよ'],['行います','行うよ'],['あります','あるよ'],['ありません','ないよ'],['なります','なるよ'],['限りません','限らないよ'],['動きます','動くよ'],['書きます','書くよ'],['読みます','読むよ'],['選べます','選べるよ'],['読めます','読めるよ'],['開けます','開けるよ'],['見られます','見られるよ'],['送信しません','送信しないよ'],['します','するよ'],['です','だよ']];
 for(const [from,to] of endings)text=text.replaceAll(from+'。',to+'。');return text;
}
