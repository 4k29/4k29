import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {createDialogueDecoder} from '../../dialogue/inference.mjs';
const [modelPath,tracePath,out]=process.argv.slice(2);
const {dialogueModel:model}=await import(pathToFileURL(modelPath));
const py=JSON.parse(fs.readFileSync(tracePath)),decoder=createDialogueDecoder(model,{tokenizerAlgorithm:'adjacent-heap'});
const rows=py.rows.map(r=>{
 const scores=decoder.logits(r.tokens),rank=[...scores].map((score,token)=>({token,score})).sort((a,b)=>b.score-a.score||a.token-b.token),maximumError=Math.max(...scores.map((v,i)=>Math.abs(v-r.pythonLogits[i])));
 return {id:r.id,firstDifferentIndex:r.firstDifferentIndex,commonPrefixTokens:r.tokens.length,pythonChosenToken:r.pythonChosenToken,javascriptChosenToken:r.javascriptChosenToken,pythonTop5:r.pythonTop5,pythonTopTwoMargin:r.pythonTopTwoMargin,javascriptTop5:rank.slice(0,5).map(x=>({...x,piece:Buffer.from(model.tokenizer.bytes[x.token],'hex').toString('utf8')})),javascriptTopTwoMargin:rank[0].score-rank[1].score,maxAbsoluteLogitError:maximumError,referenceTolerance:2e-4,referenceTolerancePassed:maximumError<=2e-4,argmaxChoicesReproduced:r.pythonTop5[0].token===r.pythonChosenToken&&rank[0].token===r.javascriptChosenToken};
});
const report={modelSha256:createHash('sha256').update(fs.readFileSync(modelPath)).digest('hex'),traceSha256:createHash('sha256').update(fs.readFileSync(tracePath)).digest('hex'),completeGreedySequenceParity:false,matchingSequences:16,totalSequences:17,rows,noOutputRepair:true,noWeightChange:true,note:'Observed full raw output divergence is retained. Close common-prefix logits can choose different maxima; reference tolerance does not establish identical autoregressive sequences.'};
fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
if(rows.some(r=>!r.referenceTolerancePassed||!r.argmaxChoicesReproduced))process.exitCode=1;
