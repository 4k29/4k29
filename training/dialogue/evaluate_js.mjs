// Full own JavaScript generation, parity and warm CPU timings, no external API.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {performance} from 'node:perf_hooks';
import {createDialogueDecoder} from './inference.mjs';
const argv=process.argv.slice(2),value=flag=>argv[argv.indexOf(flag)+1];
for(const flag of ['--model','--corpus','--out'])if(!argv.includes(flag))throw Error('Required '+flag);
const {dialogueModel}=await import(pathToFileURL(path.resolve(value('--model'))).href);
const corpus=JSON.parse(fs.readFileSync(value('--corpus'),'utf8')),decoder=createDialogueDecoder(dialogueModel);
const rows=corpus.rows.filter(r=>r.partition==='test').map(row=>{
 try{
  const result=decoder.generate(row.question,{history:row.history,maxNewTokens:128});
  return {id:row.id,kind:row.kind,question:row.question,answer:result.text,expected:row.answer,eos:result.eos,validTokens:result.validTokens,exact:result.eos&&result.validTokens&&result.text===row.answer};
 }catch(error){if(!(error instanceof RangeError))throw error;return {id:row.id,kind:row.kind,question:row.question,answer:null,exact:false,error:'context-overflow'};}
});
const questions=['MERは？','趣味は何？','Headphone (1)の重さは？'];
for(let i=0;i<20;i++)decoder.generate(questions[i%questions.length]);
const times=[];
for(let i=0;i<90;i++){const start=performance.now();decoder.generate(questions[i%questions.length]);times.push(performance.now()-start);}
times.sort((a,b)=>a-b);
const report={version:dialogueModel.version,sourceSha256:corpus.sourceSha256,total:rows.length,exact:rows.filter(r=>r.exact).length,benchmark:{samples:times.length,medianMs:times[Math.floor(times.length/2)],p95Ms:times[Math.floor(times.length*.95)],scope:'Warm local CPU generation, three profile questions, no model download, UI or network. Training contention can affect timing.'},rows};
fs.writeFileSync(value('--out'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({version:report.version,total:report.total,exact:report.exact,benchmark:report.benchmark}));
