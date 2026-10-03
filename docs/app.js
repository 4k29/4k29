import {LocalLearning} from './local-learning.js';
import { Conversation } from './dialogue.js';
import { startBoot } from './boot.js';
import { renderAnswer } from './answer-view.js';
import { QuestionJournal } from './question-journal.js';
import { mountHistory } from './history-view.js';
import { japaneseIntro } from './ui-text.js';
const journal=new QuestionJournal(),updateHistory=mountHistory(journal);
let conversation=null;
const dataReady=fetch(new URL('./profile.json',import.meta.url)).then(r=>{if(!r.ok)throw Error('profile unavailable');return r.json();}).then(data=>{conversation=new Conversation(data,{learner:new LocalLearning(data,()=>journal.records)});}).catch(()=>showError('プロフィールデータを読み込めませんでした。再読み込みしてください。'));
function showError(message){clearTimeout(errorTimer);limit.lastElementChild.textContent=message;limit.classList.remove('stage-hidden');input.setAttribute('aria-invalid','true');input.setAttribute('aria-describedby','limit');errorTimer=setTimeout(()=>{limit.classList.add('stage-hidden');input.removeAttribute('aria-invalid');input.removeAttribute('aria-describedby');},4500);}

const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const prompt=document.querySelector('.prompt'), promptText=prompt.lastElementChild;
const reply=document.querySelector('.reply'), events=document.querySelector('.events'), working=document.querySelector('.working');
let originalPrompt=promptText.textContent, originalReply=reply.lastElementChild.innerHTML;
let originalFollowup='Tell me more.',introSummary='Mostly AI-generated. Personally nitpicked. The code is a conversation. The taste is mine.';
const followup=document.querySelector('#followup'), followupText=followup.lastElementChild;
let eventTemplates=Array.from(events.children, row=>row.lastElementChild.innerHTML);
let workingText=working.children[1].textContent;
const form=document.querySelector('#prompt-form'), input=document.querySelector('#prompt-input'), send=form.querySelector('button'), chat=document.querySelector('#chat');
let errorTimer;let busy=false, run=0, limited=false;const limit=document.querySelector('#limit');
function lockSession(){languageButtons.forEach(button=>button.disabled=false);avatarState("idle");limited=conversation!==null&&conversation.history.length>=conversation.data.sessionLimit;input.disabled=false;send.disabled=false;input.placeholder=language==='jp'?japaneseIntro.placeholder:'Ask about me…';form.classList.remove('locked');}
function resetSession(){avatarState("idle");limited=false;limit.classList.add('stage-hidden');input.disabled=false;send.disabled=false;input.placeholder=language==='jp'?japaneseIntro.placeholder:'Ask about me…';form.classList.remove('locked');}

const languageButtons=Array.from(document.querySelectorAll('.language-button'));
const englishIntro={prompt:originalPrompt,reply:originalReply,followup:originalFollowup,context:document.querySelector('.context').innerHTML,events:[...eventTemplates],summary:introSummary,working:workingText,hint:working.children[2].textContent};
let language=navigator.language?.toLowerCase().startsWith('ja')?'jp':'en';
function applyLanguage(){
 const text=language==='jp'?japaneseIntro:englishIntro;
 originalPrompt=text.prompt;originalReply=text.reply;originalFollowup=text.followup;eventTemplates=[...text.events];introSummary=text.summary;workingText=text.working;
 document.documentElement.lang=language==='jp'?'ja':'en';document.querySelector('.context').innerHTML=text.context;working.children[2].textContent=text.hint;
 input.placeholder=language==='jp'?japaneseIntro.placeholder:'Ask about me…';languageButtons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.language===language)));
}
applyLanguage();languageButtons.forEach(button=>button.addEventListener('click',()=>{if(busy||button.dataset.language===language)return;language=button.dataset.language;applyLanguage();intro();}));

const avatar=document.querySelector('.avatar');
const avatarFrames={neutral:'./assets/avatar-neutral.png',blink:'./assets/avatar-blink.png',left:'./assets/avatar-left.png',right:'./assets/avatar-right.png'};
Object.values(avatarFrames).forEach(src=>{const img=new Image();img.src=src;});
let avatarMode='idle',avatarTick=0;
function avatarState(mode){avatarMode=mode;}





function faceGesture(mode,duration){avatar.classList.add(mode);setTimeout(()=>avatar.classList.remove(mode),duration);}
function scheduleBlink(){setTimeout(()=>{if(!reduced&&!document.hidden){if(Math.random()<.08){faceGesture(Math.random()<.5?'wink-left':'wink-right',320);}else{faceGesture('blinking',130);if(Math.random()<.14)setTimeout(()=>faceGesture('blinking',110),280);}}scheduleBlink();},3500+Math.random()*5500);}scheduleBlink();
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function type(el,value,delay,chunk,token){avatarState('typing');el.textContent='';if(reduced){el.textContent=value;return;}const isPrompt=el===promptText;if(isPrompt)el.classList.add('typing-caret');let i=0;while(i<value.length){if(token!==run)return;let count=isPrompt?(Math.random()<.2?2:1):Math.max(3,Math.floor(Math.random()*6)+2);const part=value.slice(i,i+count);el.append(document.createTextNode(part));i+=count;let wait=isPrompt?24+Math.random()*38:45+Math.random()*75;if(/[.!?\n]$/.test(part))wait+=isPrompt?90:180+Math.random()*240;else if(!isPrompt&&Math.random()<.1)wait+=180+Math.random()*220;await pause(wait);}el.classList.remove('typing-caret');}
function thinking(){avatarState('thinking');const el=document.createElement('div');el.className='thinking';const spin=document.createElement('span');spin.className='spinner';spin.setAttribute('aria-hidden','true');for(let i=0;i<3;i++)spin.append(document.createElement('i'));const label=document.createElement('span');label.textContent='Thinking…';el.append(spin,label);return el;}
async function intro(){if(busy)return;prompt.classList.remove('stage-hidden');resetSession();busy=true;send.disabled=true;languageButtons.forEach(button=>button.disabled=true);const token=++run;reply.classList.add('stage-hidden');followup.classList.add('stage-hidden');events.classList.add('stage-hidden');working.classList.add('stage-hidden');await type(promptText,originalPrompt,14,3,token);let wait=thinking();prompt.after(wait);await pause(reduced?0:2400);wait.remove();reply.classList.remove('stage-hidden');const text=reply.lastElementChild;text.replaceChildren();const template=document.createElement('div');template.innerHTML=originalReply;const para=template.firstElementChild;const el=document.createElement('p');text.append(el);await type(el,para.innerText,12,8,token);await pause(reduced?0:650);followup.classList.remove('stage-hidden');await type(followupText,originalFollowup,14,3,token);wait=thinking();followup.after(wait);await pause(reduced?0:3200);wait.remove();events.classList.remove('stage-hidden');for(const row of events.querySelectorAll('.generated-summary'))row.remove();for(const row of events.children){row.style.display='none';row.lastElementChild.replaceChildren();}for(let n=0;n<events.children.length;n++){const row=events.children[n];row.style.display='';const box=row.lastElementChild;const source=document.createElement('div');source.innerHTML=eventTemplates[n];for(const node of source.childNodes){if(node.nodeType===Node.TEXT_NODE){const part=document.createElement('span');box.append(part);await type(part,node.textContent,12,8,token);}else{const part=node.cloneNode(false);box.append(part);await type(part,node.textContent,12,8,token);}}await pause(reduced?0:450);}const extra=document.createElement('div');extra.className='reply generated-summary';const bullet=document.createElement('span');bullet.textContent='•';const content=document.createElement('div');extra.append(bullet,content);events.append(extra);await type(content,introSummary,12,8,token);working.classList.remove('stage-hidden');working.children[2].style.visibility='hidden';await type(working.children[1],workingText,12,8,token);working.children[2].style.visibility='';await pause(reduced?0:600);busy=false;lockSession();}
form.addEventListener('submit',async e=>{e.preventDefault();const q=input.value.trim();if(!q||busy)return;if(!conversation){showError('プロフィールデータを読み込めませんでした。再読み込みしてください。');return;}if(limited){showError('Message not sent. Usage limit reached. replay intro で新しい会話を始められます。');return;}busy=true;send.disabled=true;languageButtons.forEach(button=>button.disabled=true);chat.setAttribute('aria-busy','true');const token=++run;input.value='';input.style.height='auto';const turn=document.createElement('section');turn.className='chat-turn';const ask=document.createElement('div');ask.className='prompt';const symbol=document.createElement('span');symbol.textContent='›';const body=document.createElement('div');body.textContent=q;ask.append(symbol,body);const wait=thinking();turn.append(ask,wait);chat.append(turn);await pause(reduced?0:2600);wait.remove();const response=document.createElement('div');response.className='reply';const dot=document.createElement('span');dot.textContent='•';const output=document.createElement('div');output.className='chat-response';response.append(dot,output);turn.append(response);const answer=conversation.respond(q);journal.add(q,answer,conversation.data.unknownReply);updateHistory();await type(output,answer.text,14,5,token);renderAnswer(output,answer);busy=false;send.disabled=false;chat.setAttribute('aria-busy','false');lockSession();if(!matchMedia('(pointer: coarse)').matches)input.focus();});
document.addEventListener('pointerdown',e=>{if(!input.contains(e.target))input.blur();});
document.querySelector('#replay').addEventListener('click',()=>{if(busy)return;chat.replaceChildren();input.value='';chat.setAttribute('aria-busy','false');conversation?.reset();journal.newSession();intro();});

form.addEventListener('keydown',event=>{if(event.target===input&&event.key==='Enter'&&!event.isComposing&&event.keyCode!==229){event.preventDefault();form.requestSubmit();}});

const themeButton=document.querySelector('#theme');
const systemTheme=matchMedia('(prefers-color-scheme: light)');
let theme=systemTheme.matches?'light':'dark',themeChanged=false;
function applyTheme(){document.documentElement.dataset.theme=theme;themeButton.textContent=theme==='dark'?'☀':'☾';themeButton.setAttribute('aria-label',theme==='dark'?'ライトモードに切り替え':'ダークモードに切り替え');themeButton.title=themeButton.getAttribute('aria-label');document.querySelector('meta[name="theme-color"]').content=theme==='light'?'#fafafa':'#181818';}
applyTheme();themeButton.addEventListener('click',()=>{themeChanged=true;theme=theme==='dark'?'light':'dark';applyTheme();});
systemTheme.addEventListener('change',()=>{if(!themeChanged){theme=systemTheme.matches?'light':'dark';applyTheme();}});
startBoot(async()=>{await dataReady;document.querySelector('#profile').classList.remove('stage-hidden');intro();});
