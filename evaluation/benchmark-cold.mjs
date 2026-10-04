import fs from 'node:fs';
const start=performance.now();
const {Conversation}=await import('../docs/dialogue.js');
const moduleInitializationMs=performance.now()-start;
const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));
const questions=['名前は？','趣味は？','制作の流れは？','イヤホンとヘッドホンは？','ランニングの靴とアプリは？','サブスクは？'];
const results=questions.map(question=>{
 const c=new Conversation(data),first=performance.now(),answer=c.respond(question),firstMs=performance.now()-first,second=performance.now();c.respond(question);
 return {question,firstMs,repeatedMs:performance.now()-second,facts:answer.factIds};
});
console.log(JSON.stringify({moduleInitializationMs,results,note:'Fresh Node process, first use of each grammar. Excludes HTTP transfer and UI animations. Some later questions share previously initialized kinds.'}));
