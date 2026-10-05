// Balanced-order warm actual-history KV benchmark, independently of training.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {performance} from 'node:perf_hooks';
import assert from 'node:assert/strict';
import {createDialogueDecoder} from './inference.mjs';
const argv=process.argv.slice(2),value=flag=>argv[argv.indexOf(flag)+1];
for(const flag of ['--model','--corpus','--out'])if(!argv.includes(flag))throw Error('Required '+flag);
const {dialogueModel}=await import(pathToFileURL(path.resolve(value('--model'))).href);
const corpus=JSON.parse(fs.readFileSync(value('--corpus'),'utf8'));
const decoders={uncached:createDialogueDecoder(dialogueModel),cached:createDialogueDecoder(dialogueModel,{cachePrefixes:true})};
function conversation(decoder,probe){
 decoder.clearCache();const history=[],rows=[];
 for(const turn of probe.turns){
  const start=performance.now();let result,error;
  try{result=decoder.generate(turn.question,{history});}
  catch(problem){if(!(problem instanceof RangeError))throw problem;error='context-overflow';result={text:null,tokens:[],eos:false,validTokens:false,inputTokens:decoder.tokenizer.prompt(turn.question,history).length};}
  const elapsed=performance.now()-start;
  rows.push({text:result.text,tokens:result.tokens,eos:result.eos,validTokens:result.validTokens,inputTokens:result.inputTokens,error,elapsed,reused:decoder.cacheStats().reusedPrefixTokens});
  if(result.eos&&result.validTokens)history.push({question:turn.question,answer:result.text});
 }
 return rows;
}
// Each decoder gets the same one full warm-up; no gold history is injected.
for(const probe of corpus.conversations)for(const decoder of Object.values(decoders))conversation(decoder,probe);
const rows=[];
for(let round=0;round<6;round++)for(const [i,probe] of corpus.conversations.entries()){
 const order=(round+i)%2?['cached','uncached']:['uncached','cached'],outputs={};
 for(const mode of order)outputs[mode]=conversation(decoders[mode],probe);
 for(let turn=0;turn<probe.turns.length;turn++){
  const a=outputs.uncached[turn],b=outputs.cached[turn];
  for(const field of ['text','tokens','eos','validTokens','inputTokens','error'])assert.deepEqual(a[field],b[field]);
  rows.push({round,conversation:probe.id,turn,first:order[0],inputTokens:a.inputTokens,generatedTokens:a.tokens.length,error:a.error,uncachedMs:a.elapsed,cachedMs:b.elapsed,reusedPrefixTokens:b.reused});
 }
}
const timing=key=>{const values=rows.filter(r=>!r.error).map(r=>r[key]).toSorted((a,b)=>a-b);return {samples:values.length,medianMs:values[Math.floor(values.length/2)],p95Ms:values[Math.floor(values.length*.95)],totalMs:values.reduce((a,b)=>a+b,0)};};
const report={version:dialogueModel.version,sourceSha256:corpus.sourceSha256,cacheParity:true,rounds:6,contextOverflows:rows.filter(r=>r.error).length,timing:{uncached:timing('uncachedMs'),cached:timing('cachedMs')},scope:'Warm local CPU, six repeated passes over '+corpus.conversations.length+' fixed actual-generated-history conversations. Whole conversations alternate which decoder executes first. Includes tokenizer and all generation except prompt-overflow errors, which are counted separately; excludes model download, parsing, UI and network. This is not an accuracy test or a browser latency guarantee.',rows};
fs.writeFileSync(value('--out'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(Object.fromEntries(Object.entries(report).filter(([key])=>key!=='rows'))));
