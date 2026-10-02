// All content comes from profile.json. This is a local rule-based language generator.
const grammar={
 ja:{name:['名前は','といいます'],role:['です','として過ごしています'],tool:['を活用して開発しています','を使って制作しています'],workflow:['という流れで改善を重ねます','の順で制作を進めます'],responsibility:['は自分で担っています','を自分で考え、確認しています'],preference:['を大切にしています','を意識しています'],interest:['に関心があります','に興味を持っています'],activity:['をしています','に取り組んでいます'],product:['を愛用しています','が愛用製品です'],x:['です','で見つけられます']},
 en:{name:['My name is ','You can call me '],role:['I am ','I am currently '],tool:['I develop with ','I make things with '],workflow:['My process is ','I work through '],responsibility:['I handle ','I take care of '],preference:['I care about ','I value '],interest:['I am interested in ','My interests include '],activity:['My activities include ','I spend time on '],product:['I use ','My go-to product is '],x:['My X account is ','You can find me on X at ']}
};
function normalized(text){return text.normalize('NFKC').toLowerCase().replace(/[\s　]+/g,' ').trim();}
function matches(text,word){return /^[a-z0-9 ]+$/.test(word)?new RegExp(`(?:^|[^a-z0-9])${word.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?:$|[^a-z0-9])`,'i').test(text):text.includes(word);}
function join(values,language){if(language==='ja')return values.join('、');if(values.length<2)return values[0];return values.slice(0,-1).join(', ')+' and '+values.at(-1);}
export class Conversation{
 constructor(data){this.data=data;this.reset();}
 reset(){this.history=[];this.lastTopics=[];this.seen=new Map();this.lastReplies=[];this.turn=0;}
 detect(text){const scores=this.data.topics.map(topic=>({id:topic.id,score:topic.keywords.reduce((n,key)=>n+(matches(text,key)?(key.length>2?2:1):0),0)}));return scores.filter(t=>t.score>0).sort((a,b)=>b.score-a.score).slice(0,3).map(t=>t.id);}
 sentence(facts,language,variant){const relation=facts[0][language].relation;const value=join(facts.map(f=>f[language].value),language);const parts=grammar[language][relation];const part=parts[variant%parts.length];if(language==='en')return part+value+'.';if(relation==='name')return variant%2===0?'名前は'+value+'です。':value+'といいます。';if(relation==='x')return variant%2===0?'Xのアカウントは'+value+'です。': 'Xでは'+value+part+'。';return value+part+'。';}
 respond(question){const text=normalized(question),language=/[ぁ-んァ-ヶ一-龠]/.test(text)?'ja':'en';let topics=this.detect(text);let followup=false;
 const follow=/もっと|詳しく|それ|その|他には|続き|ほか|more|else|that|continue|detail/.test(text);
 if(!topics.length&&follow&&this.lastTopics.length){topics=[...this.lastTopics];followup=true;}
 const greeting=/^(こんにちは|こんばんは|おはよう|やあ|hello|hi|hey)[!！。\s]*$/.test(text);
 if(greeting||/^(自己紹介|紹介して|about you|introduce yourself)[?？。\s]*$/.test(text))topics=['identity','development','interests'];
 // Queries requiring missing facts stay unknown, even when they mention a known topic.
 const missing=/年齢|何歳|誕生日|生年月日|住所|住ん|学校名|どこの学校|本名|電話|メール|年収|身長|大会|タイム|なぜ|理由|どうして|いつから|age|birthday|address|school name|real name|phone|email|salary|height|why|since when/.test(text);
 let output;
 if(missing){output=language==='ja'?'その詳細はプロフィールに登録されていないので、確かなことは答えられません。':'That detail is not registered in the profile, so I cannot give a factual answer.';topics=[];}
 else if(!topics.length){output=language==='ja'?(follow?'まだ話題が決まっていません。関心、活動、開発の進め方などを聞いてみてください。':'その質問に答えられる情報はまだ登録されていません。関心、活動、デザイン、愛用製品などなら紹介できます。'):(follow?'We have not picked a topic yet. You can ask about interests, activities, or development.':'I do not have registered information to answer that. You can ask about interests, activities, design, or products.');}
 else{
 const clauses=[];for(const topic of topics){let available=this.data.facts.filter(f=>f.topic===topic);const targeted=available.filter(f=>(f.tags||[]).some(tag=>matches(text,tag))||matches(text,f[language].value));if(targeted.length&&!follow)available=targeted;
 available.sort((a,b)=>(this.seen.get(a.id)||0)-(this.seen.get(b.id)||0));const selected=available.slice(0,topic==='identity'?2:3);
 const groups=new Map();for(const fact of selected){const relation=fact[language].relation;if(!groups.has(relation))groups.set(relation,[]);groups.get(relation).push(fact);this.seen.set(fact.id,(this.seen.get(fact.id)||0)+1);}
 for(const group of groups.values())clauses.push(this.sentence(group,language,this.turn+clauses.length));}
 if(this.turn%2&&clauses.length>1)clauses.push(clauses.shift());output=clauses.join(language==='ja'?'\n':'\n');
 if(this.lastReplies.includes(output)){const clausesAgain=[];for(const topic of topics){const fact=this.data.facts.find(f=>f.topic===topic);if(fact)clausesAgain.push(this.sentence([fact],language,this.turn+1));}output=clausesAgain.join('\n');}
 this.lastTopics=topics;
 }
 this.turn++;this.lastReplies.push(output);this.lastReplies=this.lastReplies.slice(-4);this.history.push({question,answer:output,topics,language});return {text:output,topics,language};
 }
}
