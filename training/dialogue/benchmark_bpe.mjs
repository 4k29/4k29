// Same learned weights/merges/output, balanced-order warm live conversation.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {performance} from 'node:perf_hooks';
import assert from 'node:assert/strict';
import {createDialogueDecoder} from './inference.mjs';
const argv=process.argv.slice(2),value=flag=>argv[argv.indexOf(flag)+1];
for(const flag of ['--model','--corpus','--out'])if(!argv.includes(flag))throw Error('Required '+flag);
const {dialogueModel}=await import(pathToFileURL(path.resolve(value('--model'))).href),corpus=JSON.parse(fs.readFileSync(value('--corpus'),'utf8'));
const decoders={reference:createDialogueDecoder(dialogueModel,{cachePrefixes:true}),heap:createDialogueDecoder(dialogueModel,{cachePrefixes:true,tokenizerAlgorithm:'adjacent-heap'})};
function conversation(decoder,probe){
 decoder.clearCache();const history=[],rows=[];
 for(const turn of probe.turns){
  const start=performance.now();let result,error;
  try{result=decoder.generate(turn.question,{history});}
  catch(e){if(!(e instanceof RangeError))throw e;error='context-overflow';result={text:null,tokens:[],eos:false,validTokens:false,inputTokens:decoder.tokenizer.prompt(turn.question,history).length};}
  rows.push({...result,error,elapsedMs:performance.now()-start});
  if(result.eos&&result.validTokens)history.push({question:turn.question,answer:result.text});
 }
 return rows;
}
for(const probe of corpus.conversations)for(const decoder of Object.values(decoders))conversation(decoder,probe);
const rows=[];
for(let round=0;round<6;round++)for(const [index,probe] of corpus.conversations.entries()){
 const order=(round+index)%2?['heap','reference']:['reference','heap'],results={};
 for(const algorithm of order)results[algorithm]=conversation(decoders[algorithm],probe);
 for(let turn=0;turn<probe.turns.length;turn++){
  const a=results.reference[turn],b=results.heap[turn];
  for(const field of ['text','tokens','eos','validTokens','inputTokens','error'])assert.deepEqual(a[field],b[field]);
  rows.push({round,conversation:probe.id,turn,first:order[0],inputTokens:a.inputTokens,generatedTokens:a.tokens.length,error:a.error,referenceMs:a.elapsedMs,heapMs:b.elapsedMs});
 }
}
const timing=key=>{const values=rows.filter(r=>!r.error).map(r=>r[key]).toSorted((a,b)=>a-b);return {samples:values.length,medianMs:values[Math.floor(values.length/2)],p95Ms:values[Math.floor(values.length*.95)],totalMs:values.reduce((a,b)=>a+b,0)};};
const report={version:dialogueModel.version,fixtureSha256:corpus.sourceSha256,sourceSha256:dialogueModel.training.sourceSha256,tokenizerParity:true,rounds:6,contextOverflows:rows.filter(r=>r.error).length,timing:{reference:timing('referenceMs'),heap:timing('heapMs')},scope:'Warm local CPU, same own numerical model and own learned byte-BPE. Both use the same KV prefix cache. Six balanced passes over '+corpus.conversations.length+' actual-generated-history conversations; all full answers/tokens/EOS/validity/context errors must agree. Includes tokenizer and generation; excludes parsing, downloads, network and UI. Not an accuracy improvement or browser guarantee.',rows};
fs.writeFileSync(value('--out'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(Object.fromEntries(Object.entries(report).filter(([key])=>key!=='rows'))));
