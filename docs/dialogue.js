import {semanticText} from './intent-model.js';
import {normalizeQuestion,splitQuestions,analyzeQuestion} from './question-analysis.js';
import {composeAnswer} from './answer-composition.js';
import {unknownSubjects,missingFactsSentence} from './unknown-subjects.js';
export class Conversation{
 constructor(data,{learner=null}={}){this.data=data;this.learner=learner;this.reset();}
 reset(){this.history=[];this.lastTopics=[];this.lastFactIds=[];this.seen=new Map();this.lastReplies=[];this.turn=0;}
 respond(question){
  const raw=normalizeQuestion(question),text=semanticText(raw),language=/[ぁ-んァ-ヶ一-龠]/.test(raw)?'ja':'en';
  const analyses=[],context={history:this.history,lastFactIds:this.lastFactIds,lastTopics:this.lastTopics,seen:this.seen,learner:this.learner};
  for(const clause of splitQuestions(text,this.data)){
   const analysis=analyzeQuestion(clause,this.data,context);analysis.unknownSubjects=analysis.unknown?unknownSubjects(clause):[];analyses.push(analysis);
   context.lastFactIds=analysis.factIds;context.lastTopics=[...new Set(analysis.factIds.map(id=>this.data.facts.find(f=>f.id===id)?.topic).filter(Boolean))];
  }
  const ids=new Set(analyses.flatMap(a=>a.factIds));
  let selected=[...ids].map(id=>this.data.facts.find(f=>f.id===id)).filter(Boolean),topics=[];
  const hasUnknown=analyses.some(a=>a.unknown);
  let output=this.data.unknownReply||'すみません、よく分かりません';
  if(selected.length){
   topics=[...new Set(selected.map(f=>f.topic))];
   const compose=variant=>composeAnswer(selected,analyses,language,variant);
   output=compose(this.turn);if(this.lastReplies.includes(output))output=compose(this.turn+1);
   if(hasUnknown)output+='\n'+missingFactsSentence(analyses.flatMap(a=>a.unknownSubjects),language);
   for(const fact of selected)this.seen.set(fact.id,(this.seen.get(fact.id)||0)+1);
   this.lastTopics=topics;this.lastFactIds=selected.map(f=>f.id);
  }else{topics=[];this.lastTopics=[];this.lastFactIds=[];}
  const urlOnly=analyses.filter(a=>!a.unknown).every(a=>a.mode==='url-only');
  const links=selected.filter(f=>f.url).map(f=>({label:urlOnly?f.url:f[language].value,url:f.url}));
  this.turn++;this.lastReplies.push(output);this.lastReplies=this.lastReplies.slice(-4);this.history.push({question,answer:output,topics,language,factIds:selected.map(f=>f.id)});
  return {learningEligible:analyses.length===1&&!hasUnknown&&analyses[0].learningEligible===true,learned:analyses.some(a=>a.learned),text:output,topics,language,links,unanswered:hasUnknown,unansweredSubjects:analyses.flatMap(a=>a.unknownSubjects),factIds:selected.map(f=>f.id),intents:analyses.map(a=>a.intent).filter(Boolean)};
 }
}
