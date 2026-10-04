import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {gzipSync} from 'node:zlib';
import {spawnSync} from 'node:child_process';
import {Conversation} from '../docs/dialogue.js';
import {generationModel as model} from '../docs/generation-model.js';
import {neuralModel} from '../docs/neural-model.js';
import {neuralSequenceLikelihood} from '../docs/neural-inference.js';
import {generationGrammar} from '../docs/generation-grammar.js';
import {expandedIntentExamples} from '../docs/intent-expansion.js';
import {sequenceLikelihood} from '../docs/next-token-model.js';
import {tokenize} from '../training/train-generation.mjs';

const root=path.resolve(fileURLToPath(new URL('..',import.meta.url)));
const read=relative=>JSON.parse(fs.readFileSync(path.join(root,relative)));
const data=read('docs/profile.json');
const baselineArgument=process.argv.slice(2).find(arg=>!arg.startsWith('--'));
const baselineRoot=baselineArgument?path.resolve(baselineArgument):null;
const baseline=baselineRoot?{
 Conversation:(await import(pathToFileURL(path.join(baselineRoot,'docs/dialogue.js')))).Conversation,
 data:JSON.parse(fs.readFileSync(path.join(baselineRoot,'docs/profile.json')))
}:null;
function evaluate(Engine,profile,rows){
 const failures=[];
 for(const row of rows){
  const c=new Engine(profile);for(const q of row.setup||[])c.respond(q);
  const a=c.respond(row.question),sort=items=>[...items].sort(),same=(a,b)=>JSON.stringify(sort(a))===JSON.stringify(sort(b));
  if(!same(a.factIds,row.facts)||(row.unanswered!==undefined&&row.unanswered!==a.unanswered)||(row.links&&!same(a.links.map(l=>l.url),row.links))||(!row.facts.length&&a.text!==profile.unknownReply))failures.push({question:row.question,expected:row.facts,actual:a.factIds,answer:a.text});
 }
 return {correct:rows.length-failures.length,total:rows.length,failures};
}
const corpus=['questions','validation','holdout','english','english-holdout','quality','prediction'];
const regression=corpus.flatMap(file=>read('evaluation/'+file+'.json'));
const expansion=expandedIntentExamples.flatMap(row=>row.examples.map(question=>({question,facts:row.facts})));
const diversityQuestions=['名前は？','趣味は？','好きな人は？','サブスクは？','ランニングの靴は？','ランニングのアプリは？','記事では何について書いてる？'];
function diversity(Engine,profile){return diversityQuestions.map(question=>{
 const c=new Engine(profile),answers=Array.from({length:16},()=>c.respond(question));
 return {question,unique:new Set(answers.map(a=>a.text)).size,evidenceStable:answers.every(a=>JSON.stringify(a.factIds)===JSON.stringify(answers[0].factIds)&&JSON.stringify(a.links)===JSON.stringify(answers[0].links)),examples:answers.slice(0,3).map(a=>a.text)};
});}
function languageHoldout(){
 const rows=read('training/generation-holdout.json'),vocab=new Map(model.vocabulary.map((token,id)=>[token,id]));let logLoss=0,neuralLogLoss=0,tokens=0,oov=0;
 for(const row of rows){
  if(generationGrammar.some(g=>g.language===row.language&&g.template===row.template))throw Error('Training/holdout overlap: '+row.template);
  const ids=tokenize(row.template,row.language).map(token=>{if(!vocab.has(token))oov++;return vocab.get(token)??2;});
  const likelihood=sequenceLikelihood(model,row,ids);logLoss-=likelihood.logProbability;tokens+=likelihood.tokens;
  neuralLogLoss-=neuralSequenceLikelihood(row,ids).logProbability;
 }
 return {sentences:rows.length,tokens,oovTokens:oov,statisticalMeanNegativeLogLikelihood:logLoss/tokens,statisticalPerplexity:Math.exp(logLoss/tokens),neuralMeanNegativeLogLikelihood:neuralLogLoss/tokens,neuralPerplexity:Math.exp(neuralLogLoss/tokens),uniformVocabularyNegativeLogLikelihood:Math.log(neuralModel.vocabulary.length),uniformVocabularyPerplexity:neuralModel.vocabulary.length,note:'Authored unseen phrases, evaluated after freezing weights. OOV is mapped to <unk>. Uniform vocabulary is a diagnostic reference, not the previous engine or a general language-model benchmark.'};
}
function benchmark(Engine,profile){
 const timings=[],c=new Engine(profile),questions=diversityQuestions.concat(['制作の流れは？','イヤホンとヘッドホンは？','年齢は？']);
 for(let i=0;i<30;i++)c.respond(questions[i%questions.length]);
 for(let i=0;i<300;i++){const start=performance.now();c.respond(questions[i%questions.length]);timings.push(performance.now()-start);}
 timings.sort((a,b)=>a-b);return {samples:timings.length,medianMs:timings[150],p95Ms:timings[284],maxMs:timings[299],note:'Warm Node CPU response time, excludes UI animations and network loading; hardware-dependent.'};
}
function snapshotDigest(folder){
 const hash=crypto.createHash('sha256');
 for(const name of fs.readdirSync(path.join(folder,'docs')).filter(n=>/\.(?:js|json)$/.test(n)).sort())hash.update(name).update(fs.readFileSync(path.join(folder,'docs',name)));
 return hash.digest('hex');
}
const binary=fs.readFileSync(path.join(root,'docs/generation-model.js'));
const neuralBinary=fs.readFileSync(path.join(root,'docs/neural-model.js'));
const cold=spawnSync(process.execPath,[path.join(root,'evaluation/benchmark-cold.mjs')],{encoding:'utf8'});
if(cold.status!==0)throw Error('Cold benchmark failed: '+cold.stderr);
const result={model:neuralModel.version,runtime:process.version,defaultPreferences:data.responsePreferences,training:model.training,neuralTraining:neuralModel.training,preferenceWeights:Object.fromEntries(model.featureNames.map((key,i)=>[key,model.preferenceWeights[i]])),artifacts:{statisticalBytes:binary.length,statisticalGzipBytes:gzipSync(binary).length,neuralBytes:neuralBinary.length,neuralGzipBytes:gzipSync(neuralBinary).length},
 baseline:baseline?{description:'Snapshot before this prediction-model change, includes the preceding answer-quality improvement.',snapshotSha256:snapshotDigest(baselineRoot),regression:evaluate(baseline.Conversation,baseline.data,regression),expandedQuestions:evaluate(baseline.Conversation,baseline.data,expansion),diversity:diversity(baseline.Conversation,baseline.data),performance:benchmark(baseline.Conversation,baseline.data)}:null,
 current:{regression:evaluate(Conversation,data,regression),expandedQuestions:evaluate(Conversation,data,expansion),favorites:evaluate(Conversation,data,read('evaluation/favorites.json')),diversity:diversity(Conversation,data),performance:benchmark(Conversation,data),coldPerformance:JSON.parse(cold.stdout)},languageHoldout:languageHoldout(),
 scope:'Question datasets are fixed development/regression cases, including 44 new cases used for corrections. They are not an independent estimate of general question accuracy. Model paths and preference pairs are synthetic authored data, not observed user feedback.'};
const output=JSON.stringify(result,null,2)+'\n';
const out=process.argv.find(arg=>arg.startsWith('--out='));if(out)fs.writeFileSync(path.resolve(out.slice(6)),output);
const summary=e=>e?{correct:e.correct,total:e.total}:null;
console.log(JSON.stringify({baselineRegression:summary(result.baseline?.regression),currentRegression:result.current.regression,baselineExpansion:summary(result.baseline?.expandedQuestions),currentExpansion:result.current.expandedQuestions,favorites:result.current.favorites,diversity:result.current.diversity.map((r,i)=>({question:r.question,before:result.baseline?.diversity[i].unique,after:r.unique,evidenceStable:r.evidenceStable})),performance:result.current.performance,artifacts:result.artifacts,languageHoldout:result.languageHoldout},null,2));
