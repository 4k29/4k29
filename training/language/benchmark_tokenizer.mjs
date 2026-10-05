// Balanced CPU timing of exactly equivalent own BPE; no answer-quality claim.
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {createTokenizer} from '../dialogue/tokenizer.mjs';
const [mergesArg,out]=process.argv.slice(2),root=new URL('./',import.meta.url),read=p=>JSON.parse(fs.readFileSync(new URL(p,root)));
const merges=Number(mergesArg),tok=read(`bpe-${merges}/tokenizer.json`),policy=read('generation-policy.json'),reference=createTokenizer(tok),heap=createTokenizer(tok,{algorithm:'adjacent-heap'});
const samples=[...policy.probes.validation,...policy.probes.test].flatMap(p=>[{id:p.id+':opening',text:p.prefix},{id:p.id+':paragraph',text:p.referenceParagraph}]);
for(const r of samples){const a=reference.encode(r.text),b=heap.encode(r.text);if(JSON.stringify(a)!==JSON.stringify(b))throw Error('Token mismatch '+r.id);reference.encode(r.text);heap.encode(r.text);}
const rows=[];
for(let round=0;round<6;round++)for(let i=0;i<samples.length;i++){
 const sample=samples[(i+round*7)%samples.length],first=(i+round)%2?'heap':'reference',timed={};
 for(const name of [first,first==='heap'?'reference':'heap']){const begin=performance.now();const tokens=(name==='heap'?heap:reference).encode(sample.text);timed[name]={ms:performance.now()-begin,tokens};}
 if(JSON.stringify(timed.reference.tokens)!==JSON.stringify(timed.heap.tokens))throw Error('Parity failed');
 rows.push({round,id:sample.id,first,utf8Bytes:new TextEncoder().encode(sample.text).length,tokens:timed.heap.tokens.length,referenceMs:timed.reference.ms,heapMs:timed.heap.ms});
}
const stats=field=>{const values=rows.map(r=>r[field]).sort((a,b)=>a-b);return {samples:values.length,meanMs:values.reduce((n,v)=>n+v,0)/values.length,p50Ms:values[Math.floor(values.length*.5)],p95Ms:values[Math.floor(values.length*.95)]};};
const report={merges,vocabulary:tok.bytes.length,tokenizerSha256:createHash('sha256').update(fs.readFileSync(new URL(`bpe-${merges}/tokenizer.json`,root))).digest('hex'),rounds:6,tokenizerParity:true,reference:stats('referenceMs'),heap:stats('heapMs'),rows,note:'Balanced first-run order after warmup, identical complete token IDs. Tokenization alone on this CPU, not browser/network latency or a guarantee of improved answer quality.'};
fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({reference:report.reference,heap:report.heap,tokenizerParity:report.tokenizerParity}));
