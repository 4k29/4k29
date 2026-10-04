// Keep review records on this browser only. This module performs no network requests.
export const JOURNAL_KEY='4k29.question-journal.v1';
import {validPreferences} from './response-preferences.js?v=20261004-transformer-7';
export const ENGINE_VERSION='2026-10-04.transformer-7';
function browserStorage(){try{return globalThis.localStorage;}catch{return null;}}
const id=()=>globalThis.crypto?.randomUUID?.()||Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
function validRecord(record){
 if(!record||typeof record.question!=='string'||typeof record.answer!=='string'||typeof record.id!=='string'||!Number.isFinite(Date.parse(record.at)))return null;
 return {id:record.id.slice(0,80),at:record.at,session:typeof record.session==='string'?record.session.slice(0,80):'',engine:typeof record.engine==='string'?record.engine.slice(0,40):'',question:record.question.slice(0,500),answer:record.answer.slice(0,8000),language:record.language==='en'?'en':'ja',factIds:Array.isArray(record.factIds)?record.factIds.filter(v=>typeof v==='string').slice(0,40):[],intents:Array.isArray(record.intents)?record.intents.filter(v=>typeof v==='string').slice(0,20):[],unanswered:record.unanswered===true,needsReview:record.needsReview===true,learningEligible:record.learningEligible===true,learned:record.learned===true,preferenceUpdate:validPreferences(record.preferenceUpdate)};
}
export class QuestionJournal{
 constructor({storage=browserStorage(),limit=300}={}){
  this.storage=storage;this.limit=Math.max(1,Math.min(300,limit));this.records=[];this.persisted=false;this.newSession();
  try{const raw=JSON.parse(storage?.getItem(JOURNAL_KEY)||'null');if(raw?.schemaVersion===1&&Array.isArray(raw.records))this.records=raw.records.map(validRecord).filter(Boolean).slice(-this.limit);this.persisted=!!storage;}catch{}
 }
 newSession(){this.session=id();}
 save(){try{if(!this.storage)throw Error('storage unavailable');this.storage.setItem(JOURNAL_KEY,JSON.stringify({schemaVersion:1,records:this.records}));this.persisted=true;}catch{this.persisted=false;}}
 add(question,answer,unknownReply){
  const record=validRecord({id:id(),at:new Date().toISOString(),session:this.session,engine:ENGINE_VERSION,question,answer:answer.text,language:answer.language,factIds:answer.factIds,intents:answer.intents,unanswered:answer.unanswered===true||answer.text.includes(unknownReply),needsReview:false,learningEligible:answer.learningEligible,learned:answer.learned,preferenceUpdate:answer.preferenceUpdate});
  if(!record)return null;this.records.push(record);this.records=this.records.slice(-this.limit);this.save();return record;
 }
 mark(recordId,value){const record=this.records.find(r=>r.id===recordId);if(!record)return false;record.needsReview=!!value;this.save();return true;}
 clear(){this.records=[];try{if(!this.storage)throw Error('storage unavailable');this.storage.removeItem(JOURNAL_KEY);this.persisted=true;}catch{this.persisted=false;}}
 export(){return JSON.stringify({schemaVersion:1,exportedAt:new Date().toISOString(),engine:ENGINE_VERSION,records:this.records},null,2);}
}
