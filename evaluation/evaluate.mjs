import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';
const root=path.resolve(process.argv[2]||'.'),{Conversation}=await import(pathToFileURL(path.join(root,'docs/dialogue.js'))),data=JSON.parse(fs.readFileSync(path.join(root,'docs/profile.json'))),cases=JSON.parse(fs.readFileSync(new URL(process.argv[3]||'questions.json',import.meta.url)));
const results=cases.map(row=>{
 const conversation=new Conversation(data);for(const question of row.setup||[])conversation.respond(question);
 const answer=conversation.respond(row.question),actual=[...answer.factIds].sort(),expected=[...row.facts].sort(),actualLinks=answer.links.map(l=>l.url).sort();
 const correct=JSON.stringify(actual)===JSON.stringify(expected)&&(row.unanswered===undefined||row.unanswered===answer.unanswered)&&(!row.links||JSON.stringify(actualLinks)===JSON.stringify([...row.links].sort()))&&(row.facts.length>0||answer.text===data.unknownReply);
 return {...row,actual,actualUnanswered:answer.unanswered,...(row.links?{actualLinks}:{}),correct,answer:answer.text};
});
const known=results.filter(r=>r.facts.length),unknown=results.filter(r=>!r.facts.length);
console.log(JSON.stringify({total:results.length,correct:results.filter(r=>r.correct).length,knownCorrect:known.filter(r=>r.correct).length,knownTotal:known.length,unknownRejected:unknown.filter(r=>r.correct).length,unknownTotal:unknown.length,failures:results.filter(r=>!r.correct)},null,2));
