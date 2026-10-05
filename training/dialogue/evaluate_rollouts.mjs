// Actual generated history, optional exact KV reuse, no answer lookup/repair.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {performance} from 'node:perf_hooks';
import {createDialogueDecoder} from './inference.mjs';
const argv=process.argv.slice(2),value=flag=>argv[argv.indexOf(flag)+1];
for(const flag of ['--model','--corpus','--out'])if(!argv.includes(flag))throw Error('Required '+flag);
const {dialogueModel}=await import(pathToFileURL(path.resolve(value('--model'))).href);
const corpus=JSON.parse(fs.readFileSync(value('--corpus'),'utf8'));
const plain=createDialogueDecoder(dialogueModel),cached=createDialogueDecoder(dialogueModel,{cachePrefixes:true});
const conversations=[],plainTimes=[],cacheTimes=[];
function answer(decoder,question,history){
 const start=performance.now();
 try{const generated=decoder.generate(question,{history});return {...generated,milliseconds:performance.now()-start};}
 catch(error){if(!(error instanceof RangeError))throw error;return {text:null,tokens:[],eos:false,validTokens:false,inputTokens:decoder.tokenizer.prompt(question,history).length,error:'context-overflow',milliseconds:performance.now()-start};}
}
for(const conversation of corpus.conversations){
 const history=[],rows=[];cached.clearCache();
 for(const [i,turn] of conversation.turns.entries()){
  const uncached=answer(plain,turn.question,history),reused=answer(cached,turn.question,history);
  for(const key of ['text','eos','validTokens','inputTokens','error'])if(uncached[key]!==reused[key])throw Error('Cache parity failed '+conversation.id+':'+i+' '+key);
  if(JSON.stringify(uncached.tokens)!==JSON.stringify(reused.tokens))throw Error('Cache token parity failed');
  plainTimes.push(uncached.milliseconds);cacheTimes.push(reused.milliseconds);
  const exact=uncached.eos&&uncached.validTokens&&uncached.text===turn.answer;
  rows.push({question:turn.question,expected:turn.answer,answer:uncached.text,exact,eos:uncached.eos,validTokens:uncached.validTokens,error:uncached.error,inputTokens:uncached.inputTokens,generatedTokens:uncached.tokens.length,plainMs:uncached.milliseconds,cachedMs:reused.milliseconds,reusedPrefixTokens:cached.cacheStats().reusedPrefixTokens});
  if(uncached.eos&&uncached.validTokens)history.push({question:turn.question,answer:uncached.text});
 }
 conversations.push({id:conversation.id,rows,allExact:rows.every(r=>r.exact),lastExact:rows.at(-1).exact});
}
const timing=values=>{const sorted=values.toSorted((a,b)=>a-b);return {samples:sorted.length,medianMs:sorted[Math.floor(sorted.length/2)],p95Ms:sorted[Math.floor(sorted.length*.95)],totalMs:values.reduce((a,b)=>a+b,0)};};
const rows=conversations.flatMap(c=>c.rows);
const report={version:dialogueModel.version,sourceSha256:corpus.sourceSha256,conversations:conversations.length,turns:rows.length,exact:rows.filter(r=>r.exact).length,allExactConversations:conversations.filter(c=>c.allExact).length,lastExactConversations:conversations.filter(c=>c.lastExact).length,contextOverflows:rows.filter(r=>r.error==='context-overflow').length,cacheParity:true,timing:{uncached:timing(plainTimes),cached:timing(cacheTimes),scope:'One interleaved uncached/cached sequential pass, actual generated history, including initially cold execution and failures. Order can favor the second run; no causal latency or browser guarantee. Download, parsing, UI and network excluded.'},rows:conversations};
fs.writeFileSync(value('--out'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(Object.fromEntries(Object.entries(report).filter(([key])=>key!=='rows'))));
