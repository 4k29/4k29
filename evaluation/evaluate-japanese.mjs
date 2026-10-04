import fs from 'node:fs';
import {Conversation} from '../docs/dialogue.js';
import {neuralModel} from '../docs/neural-model.js';
const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));
const cases=JSON.parse(fs.readFileSync(new URL('japanese-conversation.json',import.meta.url)));
const badGrammar=/使いるよ|ありるよ|動いるよ|趣味の活動には|趣味の内容は|はイヤホン本体は|をしていますです|だよです|いるよよ|するよよ|はANCに対応だよ|接続は対応だよ|使えるです|[、,]{2}|[。]{2}/;
const thirdPerson=/本人は|と述べ|挙げています|プロフィールに|登録されています/;
const rows=[];
for(const style of ['friendly','polite'])for(const length of ['brief','normal','detail'])for(const row of cases){
 const c=new Conversation(data,{preferences:{style,length}});for(const q of row.setup)c.respond(q);
 for(let repetition=0;repetition<10;repetition++){
  const a=c.respond(row.question),criteria={
   evidence:JSON.stringify([...a.factIds].sort())===JSON.stringify([...row.facts].sort())&&a.unanswered===row.unknown,
   relevance:row.required.every(text=>a.text.includes(text))&&row.forbidden.every(text=>!a.text.includes(text)),
   grammar:!badGrammar.test(a.text),
   voice:!thirdPerson.test(a.text),
   shape:row.mode==='names'?a.text===a.factIds.map(id=>(data.facts.find(f=>f.id===id).ja.shortName||data.facts.find(f=>f.id===id).ja.value)).join('\n')&&a.links.length===0:row.mode==='unknown'?a.text===data.unknownReply:style==='polite'?!/だよ。|いるよ。/.test(a.text):true
  };
  rows.push({question:row.question,setup:row.setup,style,length,repetition,criteria,score:Object.values(criteria).filter(Boolean).length/5*100,answer:a.text});
 }
}
const failed=rows.filter(r=>r.score<100),report={model:neuralModel.version,method:'Five deterministic acceptance criteria; requires all five. Regression scoring is not an independent human fluency or general language benchmark.',criteria:['source-grounded facts and scope','question relevance and owner constraints','known grammar defects','direct owner voice','requested answer form'],questions:cases.length,replies:rows.length,passed:rows.length-failed.length,failed:failed.length,minimumScore:Math.min(...rows.map(r=>r.score)),samples:rows.filter(r=>r.repetition===0),failures:failed};
fs.writeFileSync(new URL('japanese-conversation-results.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({questions:report.questions,replies:report.replies,passed:report.passed,failed:report.failed,minimumScore:report.minimumScore}));
if(failed.length){console.log(JSON.stringify(failed.slice(0,5),null,2));process.exitCode=1;}
