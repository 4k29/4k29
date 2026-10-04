import {rankAnswerFacts,chooseWording} from './answer-priority.js?v=20261004-transformer-4';
import {semanticText} from './intent-model.js?v=20261004-transformer-4';
import {normalizeQuestion,splitQuestions,analyzeQuestion,isFollowUp} from './question-analysis.js?v=20261004-transformer-4';
import {composeAnswer} from './answer-composition.js?v=20261004-transformer-4';
import {unknownSubjects,missingFactsSentence} from './unknown-subjects.js?v=20261004-transformer-4';
import {linksForFact} from './answer-links.js?v=20261004-transformer-4';
import {createSentenceRenderer,generationVersion,generationArchitecture} from './predictive-generator.js?v=20261004-transformer-4';
import {preferenceRequest,responsePreferences,preferenceAcknowledgement} from './response-preferences.js?v=20261004-transformer-4';
import {withPublicKnowledge} from './knowledge-retrieval.js?v=20261004-transformer-4';
import {calculateQuestion} from './calculator.js?v=20261004-transformer-4';
export class Conversation{
 constructor(data,{learner=null,preferences={}}={}){this.data=withPublicKnowledge(data);this.learner=learner;this.defaultPreferences={...data.responsePreferences,...preferences};this.reset();}
 reset(){this.history=[];this.lastTopics=[];this.lastFactIds=[];this.seen=new Map();this.lastReplies=[];this.turn=0;this.preferenceEvents=[];}
 respond(question){
  const raw=normalizeQuestion(question),text=semanticText(raw),language=/[ぁ-んァ-ヶ一-龠]/.test(raw)?'ja':'en';
  const request=preferenceRequest(raw),follow=isFollowUp(text),temporaryPreference=/今回は|この回答だけ|this time|for this answer/i.test(raw);
  const preferences={...responsePreferences([...(this.learner?.records?.()||[]),...this.preferenceEvents],this.defaultPreferences),...request.update};
  if(request.update&&request.onlyInstruction&&!follow){
   if(!temporaryPreference&&!this.learner?.records)this.preferenceEvents.push({question,preferenceUpdate:request.update});
   const output=preferenceAcknowledgement(request.update,language,temporaryPreference);this.turn++;
   this.history.push({question,answer:output,topics:this.lastTopics,language,factIds:this.lastFactIds});
   return {text:output,topics:[],language,links:[],factIds:[],intents:[],unanswered:false,unansweredSubjects:[],learningEligible:false,learned:false,preferenceUpdate:temporaryPreference?null:request.update};
  }
  const analyses=[],context={history:this.history,lastFactIds:this.lastFactIds,lastTopics:this.lastTopics,seen:this.seen,learner:this.learner};
  const analyzedText=request.update&&!request.onlyInstruction?semanticText(request.remaining):text;
  for(const clause of splitQuestions(analyzedText,this.data)){
   const calculation=calculateQuestion(clause);
   if(calculation&&!this.data.facts.some(f=>f.id===calculation.id))this.data.facts.push(calculation);
   const analysis=calculation?{factIds:[calculation.id],topics:['calculation'],unknown:false,intent:'calculation',mode:'knowledge',learningEligible:false}:analyzeQuestion(clause,this.data,context);analysis.unknownSubjects=analysis.unknown?unknownSubjects(clause):[];analyses.push(analysis);
   context.lastFactIds=analysis.factIds;context.lastTopics=[...new Set(analysis.factIds.map(id=>this.data.facts.find(f=>f.id===id)?.topic).filter(Boolean))];
  }
  const ids=new Set(analyses.flatMap(a=>a.factIds));
  let selected=[...ids].map(id=>this.data.facts.find(f=>f.id===id)).filter(Boolean),topics=[];
  const hasUnknown=analyses.some(a=>a.unknown);
  const preferenceUpdate=request.update&&!follow&&!hasUnknown&&!temporaryPreference?request.update:null;
  if(preferenceUpdate&&!this.learner?.records)this.preferenceEvents.push({question,preferenceUpdate});
  let output=this.data.unknownReply||'すみません、よく分かりません';
  let generation=null;
  if(selected.length){
   selected=rankAnswerFacts(selected,analyses);topics=[...new Set(selected.map(f=>f.topic))];
   const renderer=createSentenceRenderer({...preferences,question:raw,previous:this.lastReplies}),scores=new Map();
   const compose=variant=>{const start=renderer.trace.length,result=composeAnswer(selected,analyses,language,variant,{renderer,...preferences}),steps=renderer.trace.slice(start);scores.set(result,steps.reduce((n,s)=>n+s.score,0)/(steps.length||1));return result;};
   output=chooseWording(compose,this.turn,this.lastReplies,{quality:result=>scores.get(result)||0});
   generation={model:generationVersion,algorithm:generationArchitecture,style:preferences.style,length:preferences.length,method:renderer.trace.length?'constrained-next-token':'registered-value'};
   if(hasUnknown)output+='\n'+missingFactsSentence(analyses.flatMap(a=>a.unknownSubjects),language);
   for(const fact of selected)this.seen.set(fact.id,(this.seen.get(fact.id)||0)+1);
   this.lastTopics=topics;this.lastFactIds=selected.map(f=>f.id);
  }else{topics=[];this.lastTopics=[];this.lastFactIds=[];}
  const urlOnly=analyses.filter(a=>!a.unknown).every(a=>a.mode==='url-only');
  const links=selected.flatMap(f=>{const requests=analyses.filter(a=>!a.unknown&&a.factIds.includes(f.id));return requests.every(a=>a.mode==='value-only')?[]:[...(f.url?[{label:urlOnly?f.url:f[language].value,url:f.url}]:[]),...linksForFact(f,analyses)];});
  this.turn++;this.lastReplies.push(output);this.lastReplies=this.lastReplies.slice(-8);this.history.push({question,answer:output,topics,language,factIds:selected.map(f=>f.id)});
  return {learningEligible:analyses.length===1&&!hasUnknown&&!request.update&&analyses[0].learningEligible===true,learned:analyses.some(a=>a.learned),text:output,topics,language,links,unanswered:hasUnknown,unansweredSubjects:analyses.flatMap(a=>a.unknownSubjects),factIds:selected.map(f=>f.id),intents:analyses.map(a=>a.intent).filter(Boolean),preferenceUpdate,generation};
 }
}
