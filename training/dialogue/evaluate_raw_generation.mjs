// Own raw-document greedy continuation; no question wrapper, lookup or repair.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createDialogueDecoder} from './inference.mjs';
const argv=process.argv.slice(2),value=flag=>argv[argv.indexOf(flag)+1];
for(const flag of ['--model','--corpus','--out'])if(!argv.includes(flag))throw Error('Required '+flag);
const {dialogueModel}=await import(pathToFileURL(path.resolve(value('--model'))).href),corpus=JSON.parse(fs.readFileSync(value('--corpus'),'utf8'));
const d=createDialogueDecoder(dialogueModel,{cachePrefixes:true}),rows=[];
for(const row of corpus.rows){
 d.clearCache();const input=[d.tokenizer.specials.bos,...d.tokenizer.encode(row.prefix)],tokens=[];let stop='token-limit',eos=false;
 for(let i=0;i<Math.min(80,dialogueModel.config.context-input.length);i++){
  const scores=d.logits([...input,...tokens]);let best=0;for(let j=1;j<scores.length;j++)if(scores[j]>scores[best])best=j;
  if(best===d.tokenizer.specials.eos){eos=true;stop='eos';break;}tokens.push(best);
  // Stop after the token containing the first generated sentence mark; do not
  // clip its bytes, change it, force punctuation or constrain any candidate.
  if(d.tokenizer.decode(tokens).includes('。')){stop='sentence-mark';break;}
 }
 let validUtf8=true;try{d.tokenizer.decode(tokens,{fatal:true});}catch{validUtf8=false;}
 rows.push({...row,continuation:d.tokenizer.decode(tokens),tokens,eos,stop,inputTokens:input.length,validTokens:validUtf8&&tokens.every(id=>id>=6)});
}
const report={version:dialogueModel.version,sourceSha256:corpus.sourceSha256,total:rows.length,validTokens:rows.filter(r=>r.validTokens).length,scope:'Raw BOS+source prefix, own tokenizer and unconstrained full-vocabulary argmax. Stops at first generated sentence-mark token, EOS or80 tokens; never modifies text. Source reference is not an exact target; fluency must be inspected. No chat or factual accuracy claim.',rows};
fs.writeFileSync(value('--out'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({version:report.version,total:report.total,validTokens:report.validTokens}));
