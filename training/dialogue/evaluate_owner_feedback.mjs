// Latest owner-reported regressions; diagnostic only, never answer retrieval.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createDialogueDecoder} from './inference.mjs';
const argv=process.argv.slice(2),value=flag=>argv[argv.indexOf(flag)+1];
for(const flag of ['--model','--out'])if(!argv.includes(flag))throw Error('Required '+flag);
const {dialogueModel}=await import(pathToFileURL(path.resolve(value('--model'))).href);
const fixture=JSON.parse(fs.readFileSync(new URL('./switch-owner-feedback.json',import.meta.url))),d=createDialogueDecoder(dialogueModel);
const rows=fixture.rows.map(row=>{
 const r=d.generate(row.question),text=r.text;
 const criteria={complete:r.eos&&r.validTokens,japanese:/[ぁ-んァ-ヶ一-龠]/.test(text),
  required:row.required.every(word=>text.includes(word)),
  forbidden:row.forbidden.every(word=>!text.includes(word)),
  intent:row.intentTerms.length===0||row.intentTerms.some(word=>text.includes(word))};
 if(row.namesOnly){let rest=text;for(const word of row.required.toSorted((a,b)=>b.length-a.length))rest=rest.replaceAll(word,'');criteria.namesOnly=!rest.replace(/[\s、,。・と]/g,'');}
 return {id:row.id,question:row.question,answer:text,eos:r.eos,validTokens:r.validTokens,criteria,passed:Object.values(criteria).every(Boolean)};
});
const report={version:dialogueModel.version,corpusSha256:dialogueModel.training.sourceSha256,feedbackSource:fixture.provenance,total:rows.length,passed:rows.filter(r=>r.passed).length,scope:'Latest user-reported regressions against the current owner requirements. Some questions can occur in old QA data; development diagnostics, not fresh holdout. Literal criteria are necessary checks, not full semantic or human evaluation. Requirements and generated outputs never supply inference answers or training targets.',rows};
fs.writeFileSync(value('--out'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({version:report.version,total:report.total,passed:report.passed}));
