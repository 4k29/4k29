import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {Conversation} from '../docs/dialogue.js';import {semanticModel} from '../docs/intent-model.js';
const data=JSON.parse(fs.readFileSync(new URL('../docs/profile.json',import.meta.url)));
const cases=[
 [['あなた誰？','あなたは誰ですか？','君はだれ？','きみって誰なの？','あんた誰やねん？','誰？','誰なんだ？','誰ですか？','どなたでしょうか？','あなたは誰でしょうか？','ねぇ、君って誰なの？','誰なのか教えて','誰なのか知りたい','Who are you?','who r u?','Who is this?','Tell me who you are','What is your name?','なんてお呼びすればいい？','何と呼ぶの？'],['name']],
 [['あなたって何者なの？','どういう人なの？','あなたのこと教えて','Can you introduce yourself?','Tell me about yourself','どんな人ですか？'],['name','student','workflow','tecirc','photo','running']],
 [['職業は何ですか？','あなた学生なの？','社会人なの？','会社員ですか？','What do you do for work?','あなた何してる人？'],['student']],
 [['普段何してる？','あなた何してる？','休日どう過ごす？','趣味って何？','What are your hobbies?','What do you do for fun?'],['tecirc','photo','running']],
 [['何に興味がありますか？','What are your interests?','何に夢中？'],['apple','nothing','openai','tech','ui','design','hci','slm','context']],
 [['何が好き？','好きなものは？','What do you like?'],['apple','nothing','openai','tech','ui','design','hci','slm','context','favorite-vivant','favorite-kyu','favorite-tokyo-mer','favorite-person']],
 [['好きなメーカーは？','どんなブランドに興味がある？','What are your favorite brands?'],['apple','nothing','openai','favorite-kyu']],
 [['デザインに興味がある？','デザインが好き？'],['design']],
 [['UIとUXに関心ある？'],['ui']],
 [['作品を作る時の流れを具体的に説明して','どうやって作品を作る？','制作をどんな手順で進める？','How do you create things?','アイデアを形にするときはどう進める？'],['workflow','iteration','taste']],
 [['AIに全部任せてるの？自分では何をしてる？','AIと人間の役割分担を教えて','AIに丸投げなの？','人間側は何を担当する？','自分は何をしてる？'],['workflow','taste']],
 [['何を使って開発してる？','開発にはどのAIを使ってる？','Which tools do you use to develop?'],['workflow']],
 [['学生だけど何を作ってる？','What do you make?','どんな作品を作る？'],['tecirc','photo']],
 [['このサイト誰が作った？','誰がこのサイトを作ったの？'],['name','workflow','taste']],
 [['UIを作るとき大切にしてるのは？','使いやすいデザインのために意識してることは？'],['defaults','spacing']],
 [['記事では何について書いてる？','What topics do your articles cover?'],['tecirc','tecirc-subjects','tecirc-link']],
 [['記事は何処で読める？','Where can I read your articles?'],['tecirc-link']],
 [['このチャットの回答はどう組み立ててる？','このチャットって生成AIにつながってる？'],['site-engine']],
 [['このチャットは何の言語で実装してる？'],['site-stack']],
 [['このサイトの会話は外部に送信する？'],['site-privacy']],
 [['Twitterの名前は？'],['x','x-secondary']],
];
for(const [questions,ids] of cases)for(const question of questions)test('intent regression: '+question,()=>{
 const answer=new Conversation(data).respond(question);assert.deepEqual(new Set(answer.factIds),new Set(ids));assert.notEqual(answer.text,data.unknownReply);assert.equal(answer.text.includes(data.unknownReply),false);for(const id of ids){if(id==='tecirc'&&answer.intents.includes('article-subjects')){assert.match(answer.text,/Tecirc/);assert.ok(answer.links.some(link=>link.url==='https://4k29.github.io/tecirc/notes/'));}else assert.ok(answer.text.includes(data.facts.find(f=>f.id===id)[answer.language].value));}
});
test('advanced questions combine compatible registered relations rather than a generic topic',()=>{
 const c=new Conversation(data);
 let a=c.respond('UIのデザインで大切なことと、制作をどう進めるか説明して');assert.deepEqual(new Set(a.factIds),new Set(['defaults','spacing','workflow','iteration','taste']));
 a=c.respond('このチャットの実装言語と回答を生成する仕組みは？');assert.deepEqual(new Set(a.factIds),new Set(['site-stack','site-engine']));
 a=c.respond('AIと役割分担しながらどんな手順で作ってる？');assert.deepEqual(new Set(a.factIds),new Set(['workflow','taste','iteration']));
});
test('context in the same question and a subsequent turn resolves registered antecedents',()=>{
 const c=new Conversation(data);let a=c.respond('サブ垢は？そのリンクは？');assert.deepEqual(a.factIds,['x-secondary']);assert.equal(a.links[0].url,'https://x.com/uma_4k');
 c.respond('制作の流れは？');a=c.respond('それはどういう流れで作ってる？');assert.deepEqual(new Set(a.factIds),new Set(['workflow','iteration','taste']));
});
test('brief requests shorten an introduction without discarding identity',()=>{
 const a=new Conversation(data).respond('あなたについて簡単に教えて');assert.deepEqual(a.factIds,['name','student','workflow']);
});
test('unregistered details and third-person questions remain unknown',()=>{
 for(const q of ['私は誰？','私の名前は？','友達の名前は？','あなたの本名は？','AIを使い始めたきっかけは？','AIを使う理由は？','どの会社で働いてる？','どのメーカーが一番好き？','学生の専攻は？','写真のカメラの型番は？'])assert.equal(new Conversation(data).respond(q).text,data.unknownReply,q);
});
test('every semantic-model outcome refers to an existing fact, and changing facts changes the answer',()=>{
 const ids=new Set(data.facts.map(f=>f.id));for(const rule of semanticModel.intents)for(const id of rule.facts)assert.ok(ids.has(id));
 const clone=structuredClone(data);clone.facts.find(f=>f.id==='name').ja.value='差し替え名';assert.match(new Conversation(clone).respond('あなた誰？').text,/差し替え名/);
});
test('conceptual development questions and chat privacy retain the correct subject',()=>{
 let c=new Conversation(data);assert.deepEqual(new Set(c.respond('どんな考え方で開発してる？').factIds),new Set(['workflow','iteration','taste']));
 assert.deepEqual(c.respond('このチャットはAIで回答してるけど外部に送信する？').factIds,['site-privacy']);
 assert.deepEqual(c.respond('AIにこのチャットの回答を全部任せてる？').factIds,['site-engine']);
});
