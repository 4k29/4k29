// Raw FP32 checkpoint diagnostic only. No weight rounding, optimizer or repair.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createDialogueDecoder} from '../../dialogue/inference.mjs';

const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const [requestPath,outputPath]=process.argv.slice(2);
if(!requestPath||!outputPath)throw Error('Usage: node parity.mjs REQUEST_JSON NEW_OUTPUT_JSON');
if(fs.existsSync(outputPath))throw Error('Refuse raw parity output overwrite');
const request=read(requestPath),metadata=read(request.metadataPath);
if(sha(fs.readFileSync(fileURLToPath(import.meta.url)))!==request.expectedRunnerSha256)throw Error('Runner SHA mismatch');
const binary=fs.readFileSync(metadata.binaryPath);
if(binary.length!==metadata.bytes||sha(binary)!==metadata.binarySha256)throw Error('Exact FP32 binary SHA/length mismatch');
const endian=new Uint32Array([0x01020304]);
if(new Uint8Array(endian.buffer)[0]!==4)throw Error('This exact raw-FP32 loader requires little-endian host');
let backing=binary;
if(backing.byteOffset%4!==0)backing=Uint8Array.from(binary);
const values=new Float32Array(backing.buffer,backing.byteOffset,backing.byteLength/4);
const tensors={};
for(const [name,spec]of Object.entries(metadata.tensors)){
 const n=spec.shape.reduce((a,b)=>a*b,1);
 if(n!==spec.floatCount||spec.floatOffset<0||spec.floatOffset+n>values.length)throw Error('Invalid tensor extent');
 tensors[name]={shape:spec.shape,data:values.subarray(spec.floatOffset,spec.floatOffset+n)};
}
// The actual numeric IDs are unchanged. API-only names keep the existing
// tokenizer's six-special byte offset; no question formatting is called.
const tokenizer={...metadata.tokenizer,specials:{pad:0,bos:1,eos:2,user:3,assistant:4,turn:5}};
const decoder=createDialogueDecoder({version:'own-v2-raw-parity',config:metadata.config,tokenizer,tensors},{cachePrefixes:true});
function score(tokens){
 const logits=decoder.logits(tokens);
 if(!Array.from(logits).every(Number.isFinite))throw Error('Nonfinite JS logits');
 let best=0;for(let i=1;i<logits.length;i++)if(logits[i]>logits[best])best=i;
 let second=-Infinity;for(let i=0;i<logits.length;i++)if(i!==best)second=Math.max(second,logits[i]);
 return {logits:Array.from(logits),argmax:best,topTwoLogitGap:logits[best]-second};
}
const rows=[];
for(const c of request.cases){
 decoder.clearCache();
 const forced=c.pythonHistoryInputs.map((tokens,position)=>({position,inputTokens:tokens,...score(tokens)}));
 // Returning to the original prefix truncates the causal cache before any
 // Python-generated future token; reuse cannot feed those future tokens.
 const tokens=[],steps=[];
 for(let position=0;position<request.maxNewTokens;position++){
  const input=c.prefixTokens.concat(tokens),result=score(input);
  steps.push({position,inputTokens:input,...result});tokens.push(result.argmax);
  if(result.argmax===2)break;
 }
 rows.push({id:c.id,referencePythonHistoryScores:forced,
  independentAutoregression:{tokensIncludingEos:tokens,eos:tokens.at(-1)===2,steps},cache:decoder.cacheStats()});
}
const result={scope:'Three fixed full prefixes, at most four greedy tokens; not full192/all32 parity',
 checkpointSha256:metadata.checkpointSha256,binarySha256:sha(binary),rawBinaryExactVerified:true,
 weightDtype:'IEEE754-float32-little-endian-no-rounding',node:process.version,rows};
fs.writeFileSync(outputPath,JSON.stringify(result,null,2)+'\n');
