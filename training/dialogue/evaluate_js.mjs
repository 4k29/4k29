// Full own JavaScript generation, parity and warm CPU timings, no external API.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {performance} from 'node:perf_hooks';
import {createDialogueDecoder} from './inference.mjs';
const argv=process.argv.slice(2),value=flag=>argv[argv.indexOf(flag)+1];
for(const flag of ['--model','--corpus','--out'])if(!argv.includes(flag))throw Error('Required '+flag);
const beamSize=argv.includes('--beam-size')?Number(value('--beam-size')):1;
const lengthPenalty=argv.includes('--length-penalty')?Number(value('--length-penalty')):0.6;
if(!Number.isInteger(beamSize)||beamSize<1||beamSize>16||!Number.isFinite(lengthPenalty)||lengthPenalty<0)throw Error('Invalid beam settings');
const {dialogueModel}=await import(pathToFileURL(path.resolve(value('--model'))).href);
const corpus=JSON.parse(fs.readFileSync(value('--corpus'),'utf8')),decoder=createDialogueDecoder(dialogueModel);
const generate=(question,options={})=>beamSize===1?decoder.generate(question,options):decoder.generateBeam(question,{...options,beamSize,lengthPenalty});
const corpusTimes=[];
const rows=corpus.rows.filter(r=>r.partition==='test').map(row=>{
 try{
  const started=performance.now();
  const result=generate(row.question,{history:row.history});
  const generationMs=performance.now()-started;corpusTimes.push(generationMs);
  return {id:row.id,kind:row.kind,question:row.question,answer:result.text,expected:row.answer,eos:result.eos,validTokens:result.validTokens,exact:result.eos&&result.validTokens&&result.text===row.answer,inputTokens:result.inputTokens,generatedTokens:result.tokens.length,generationMs};
 }catch(error){if(!(error instanceof RangeError))throw error;return {id:row.id,kind:row.kind,question:row.question,answer:null,exact:false,error:'context-overflow'};}
});
const questions=['MERは？','趣味は何？','Headphone (1)の重さは？'];
for(let i=0;i<20;i++)generate(questions[i%questions.length]);
const times=[];
for(let i=0;i<90;i++){const start=performance.now();generate(questions[i%questions.length]);times.push(performance.now()-start);}
times.sort((a,b)=>a-b);
corpusTimes.sort((a,b)=>a-b);
const report={version:dialogueModel.version,sourceSha256:corpus.sourceSha256,total:rows.length,exact:rows.filter(r=>r.exact).length,benchmark:{samples:times.length,medianMs:times[Math.floor(times.length/2)],p95Ms:times[Math.floor(times.length*.95)],scope:'Warm local CPU generation, three profile questions, no model download, UI or network. Training contention can affect timing.'},corpusBenchmark:{samples:corpusTimes.length,medianMs:corpusTimes[Math.floor(corpusTimes.length/2)],p95Ms:corpusTimes[Math.floor(corpusTimes.length*.95)],maximumMs:corpusTimes.at(-1),scope:'One sequential pass over all evaluated questions and histories after model parsing. Includes initially cold execution and failures up to the context cap; excludes model download, parsing, UI and network. Not a browser guarantee.'},rows};
if(beamSize>1){
 report.decoding={method:'beam',beamSize,lengthPenalty,scope:'Full vocabulary search with at most this many active branches. EOS paths may finish at any step. No factual or grammatical constraints; not a global optimum guarantee.'};
 report.training=dialogueModel.training;
 const sourceRows=new Map(corpus.rows.map(r=>[r.id,r]));
 for(const row of rows)row.history=sourceRows.get(row.id).history;
}
fs.writeFileSync(value('--out'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({version:report.version,total:report.total,exact:report.exact,decoding:report.decoding,benchmark:report.benchmark,corpusBenchmark:report.corpusBenchmark}));
