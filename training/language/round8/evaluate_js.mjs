// Own numerical implementation, raw opening only; no retrieval/templates/API.
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {createDialogueDecoder} from '../../dialogue/inference.mjs';
const [modelPath,pythonPath,out]=process.argv.slice(2);
const {dialogueModel:model}=await import(pathToFileURL(modelPath));
const py=JSON.parse(fs.readFileSync(pythonPath)),decoder=createDialogueDecoder(model,{tokenizerAlgorithm:'adjacent-heap'}),rows=[];
for(const row of py.rows){const begin=performance.now();const result=decoder.generateRaw(row.prefix,{maxNewTokens:py.maxNewTokens});rows.push({id:row.id,prefix:row.prefix,...result,elapsedMs:performance.now()-begin});}
const references=(py.references||[]).map(row=>{const scores=decoder.logits(row.tokens);return {id:row.id,maxAbsoluteError:Math.max(...scores.map((v,i)=>Math.abs(v-row.logits[i])))};});
const report={version:model.version,modelSha256:createHash('sha256').update(fs.readFileSync(modelPath)).digest('hex'),rows,references,completeGenerationParity:rows.every((r,i)=>['text','tokens','eos','validUtf8','validTokens','inputTokens'].every(k=>JSON.stringify(r[k])===JSON.stringify(py.rows[i][k])))};
fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({rows:rows.length,completeGenerationParity:report.completeGenerationParity,references}));
if(!report.completeGenerationParity||references.some(r=>r.maxAbsoluteError>.0002))process.exitCode=1;
