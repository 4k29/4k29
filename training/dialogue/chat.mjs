// Local experimental dialogue, using only our tokenizer and Transformer.
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createInterface} from 'node:readline/promises';
import {stdin,stdout} from 'node:process';
import {createDialogueDecoder} from './inference.mjs';
const argv=process.argv.slice(2),value=flag=>{const i=argv.indexOf(flag);return i<0?undefined:argv[i+1];};
const file=value('--model')||'training/dialogue/web-replay-candidate.js';
const {dialogueModel}=await import(pathToFileURL(path.resolve(file)).href);
const decoder=createDialogueDecoder(dialogueModel);
const question=value('--question');
if(question!==undefined){
 const result=decoder.generate(question);stdout.write(result.text+'\n');
 if(!result.eos||!result.validTokens)process.exitCode=2;
}else{
 const rl=createInterface({input:stdin,output:stdout}),history=[];
 stdout.write('未公開の試作モデルです。誤回答があります。/resetで会話を消去、/quitで終了します。\n');
 try{
  while(true){
   const q=(await rl.question('質問 > ')).trim();if(!q)continue;
   if(['/quit','/exit'].includes(q))break;
   if(q==='/reset'){history.length=0;stdout.write('会話を消去しました。\n');continue;}
   try{
    const result=decoder.generate(q,{history});stdout.write(result.text+'\n');
    if(result.eos&&result.validTokens)history.push({question:q,answer:result.text});
    else stdout.write('回答を最後まで生成できませんでした。\n');
   }catch(error){
    if(error instanceof RangeError)stdout.write('入力がモデルの文脈長を超えました。/resetで新しい会話を始められます。\n');
    else throw error;
   }
  }
 }finally{rl.close();}
}
