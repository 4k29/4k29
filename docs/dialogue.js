import {semanticText} from './intent-model.js?v=20261003-answer-fix-2';
import {normalizeQuestion,splitQuestions,analyzeQuestion} from './question-analysis.js?v=20261003-answer-fix-2';
import {composeAnswer} from './answer-composition.js?v=20261003-answer-fix-2';
import {unknownSubjects,missingFactsSentence} from './unknown-subjects.js?v=20261003-answer-fix-2';
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
  const modes=analyses.map(a=>a.mode);
  const links=selected.flatMap(f=>[...(f.url?[{label:urlOnly?f.url:f[language].value,url:f.url}]:[]),...(f.links||[]).filter(l=>modes.includes('favorite-youtube')?l.channel==='youtube':modes.includes('favorite-x')?l.channel==='x':true)]);
  this.turn++;this.lastReplies.push(output);this.lastReplies=this.lastReplies.slice(-4);this.history.push({question,answer:output,topics,language,factIds:selected.map(f=>f.id)});
  return {learningEligible:analyses.length===1&&!hasUnknown&&analyses[0].learningEligible===true,learned:analyses.some(a=>a.learned),text:output,topics,language,links,unanswered:hasUnknown,unansweredSubjects:analyses.flatMap(a=>a.unknownSubjects),factIds:selected.map(f=>f.id),intents:analyses.map(a=>a.intent).filter(Boolean)};
 }
}
