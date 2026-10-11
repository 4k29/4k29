import {memories} from './memories.js?v=20261011-editor-1';
import {LocalLearning} from './local-learning.js?v=20261011-editor-1';
import {Conversation} from './dialogue.js?v=20261011-editor-1';
import {renderAnswer} from './answer-view.js?v=20261011-editor-1';
import {QuestionJournal} from './question-journal.js?v=20261011-editor-1';

const journal=new QuestionJournal();
const dialog=document.querySelector('#chat-dialog');
const form=document.querySelector('#prompt-form'),input=document.querySelector('#prompt-input'),send=form.querySelector('button');
const chat=document.querySelector('#chat'),limit=document.querySelector('#limit');
const replay=document.querySelector('#replay'),openChat=document.querySelector('#open-chat');
let conversation=null,busy=false,language='jp',errorTimer;
function showError(message){clearTimeout(errorTimer);limit.textContent=message;limit.hidden=false;input.setAttribute('aria-invalid','true');input.setAttribute('aria-describedby','limit');errorTimer=setTimeout(()=>{limit.hidden=true;input.removeAttribute('aria-invalid');input.removeAttribute('aria-describedby');},4500);}
const dataReady=fetch(new URL('./profile.json?v=20261011-editor-1',import.meta.url)).then(r=>{if(!r.ok)throw Error('profile unavailable');return r.json();}).then(data=>{conversation=new Conversation(data,{learner:new LocalLearning(data,()=>journal.records)});input.disabled=false;send.disabled=false;}).catch(()=>showError('プロフィールを読み込めませんでした。再読み込みしてください。'));
function applyLanguage(){document.documentElement.lang=language==='jp'?'ja':'en';document.querySelectorAll('[data-language]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.language===language)));document.querySelectorAll('[data-jp]').forEach(el=>el.textContent=el.dataset[language]);input.placeholder=language==='jp'?'質問…':'Ask…';input.setAttribute('aria-label',language==='jp'?'質問':'Question');send.setAttribute('aria-label',language==='jp'?'送信':'Send');openChat.setAttribute('aria-label',language==='jp'?'しかについて聞く':'Ask about Shika');document.querySelector('#close-chat').setAttribute('aria-label',language==='jp'?'会話を閉じる':'Close conversation');replay.setAttribute('aria-label',language==='jp'?'会話をリセット':'Reset conversation');}
document.querySelectorAll('[data-language]').forEach(b=>b.addEventListener('click',()=>{language=b.dataset.language;applyLanguage();}));applyLanguage();
const desktopChat=matchMedia('(min-width:1101px)');
function closeSidebar(){dialog.close();document.body.classList.remove('chat-open');openChat.setAttribute('aria-expanded','false');openChat.focus({preventScroll:true});}
function openSidebar(){if(dialog.open)return;dialog.setAttribute('aria-modal',String(!desktopChat.matches));if(desktopChat.matches)dialog.show();else dialog.showModal();document.body.classList.add('chat-open');openChat.setAttribute('aria-expanded','true');if(!input.disabled)input.focus({preventScroll:true});}
openChat.addEventListener('click',()=>dialog.open?closeSidebar():openSidebar());
document.querySelector('#close-chat').addEventListener('click',closeSidebar);
dialog.addEventListener('cancel',e=>{e.preventDefault();closeSidebar();});
dialog.addEventListener('close',()=>{if(!dialog.open){document.body.classList.remove('chat-open');openChat.setAttribute('aria-expanded','false');}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&dialog.open&&desktopChat.matches){e.preventDefault();closeSidebar();}});
dialog.addEventListener('click',e=>{if(e.target!==dialog||desktopChat.matches)return;const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeSidebar();});
desktopChat.addEventListener('change',()=>{if(dialog.open){const active=document.activeElement;dialog.close();openSidebar();if(active&&dialog.contains(active))active.focus({preventScroll:true});}});
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function type(el,value){if(reduced.matches){el.textContent=value;return;}for(let i=0;i<value.length;i+=8){el.append(document.createTextNode(value.slice(i,i+8)));await pause(24);}}
function thinking(){const el=document.createElement('div');el.className='thinking';const dots=document.createElement('span');dots.className='spinner';dots.setAttribute('aria-hidden','true');for(let i=0;i<3;i++)dots.append(document.createElement('i'));const label=document.createElement('span');label.textContent=language==='jp'?'考えています…':'Thinking…';el.append(dots,label);return el;}
function resizeQuestion(){input.style.height='auto';input.style.height=Math.min(input.scrollHeight,160)+'px';input.style.overflowY=input.scrollHeight>160?'auto':'hidden';}
input.addEventListener('input',resizeQuestion);window.addEventListener('resize',resizeQuestion);
form.addEventListener('keydown',e=>{if(e.target===input&&e.key==='Enter'&&!e.shiftKey&&!e.isComposing&&e.keyCode!==229){e.preventDefault();form.requestSubmit();}});
form.addEventListener('submit',async e=>{e.preventDefault();const question=input.value.trim();if(!question||busy)return;await dataReady;if(!conversation){showError(language==='jp'?'再読み込みしてください。':'Please reload the page.');return;}if(conversation.history.length>=conversation.data.sessionLimit){showError(language==='jp'?'会話の上限に達しました。リセットで再開できます。':'Usage limit reached. Reset to start again.');return;}
 busy=true;send.disabled=true;replay.disabled=true;chat.setAttribute('aria-busy','true');input.value='';resizeQuestion();
 const turn=document.createElement('section');turn.className='chat-turn';const ask=document.createElement('div');ask.className='prompt';const marker=document.createElement('span');marker.textContent='›';marker.setAttribute('aria-hidden','true');const text=document.createElement('div');text.textContent=question;ask.append(marker,text);const wait=thinking();turn.append(ask,wait);chat.append(turn);
 try{await pause(reduced.matches?0:450);const answer=conversation.respond(question);journal.add(question,answer,conversation.data.unknownReply);wait.remove();const response=document.createElement('div');response.className='reply';const dot=document.createElement('span');dot.textContent='·';dot.setAttribute('aria-hidden','true');const output=document.createElement('div');output.className='chat-response';response.append(dot,output);turn.append(response);await type(output,answer.text);renderAnswer(output,answer);}catch{wait.remove();showError(language==='jp'?'うまく答えられませんでした。もう一度試してください。':'Please try again.');}finally{busy=false;send.disabled=false;replay.disabled=false;chat.setAttribute('aria-busy','false');if(dialog.open&&!matchMedia('(pointer: coarse)').matches)input.focus();}
});
replay.addEventListener('click',()=>{if(busy)return;conversation?.reset();journal.newSession();chat.replaceChildren();limit.hidden=true;input.value='';resizeQuestion();input.focus();});
const themeButton=document.querySelector('#theme'),systemTheme=matchMedia('(prefers-color-scheme: dark)');
let theme=systemTheme.matches?'dark':'light',themeChanged=false;
function applyTheme(){document.documentElement.dataset.theme=theme;themeButton.innerHTML=theme==='dark'?'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg>':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 14A9 9 0 0 1 10 3.5 9 9 0 1 0 20.5 14Z"/></svg>';themeButton.setAttribute('aria-label',theme==='dark'?'ライトモードに切り替え':'ダークモードに切り替え');themeButton.title=themeButton.getAttribute('aria-label');document.querySelector('meta[name="theme-color"]').content=theme==='dark'?'#0e100e':'#f3f1eb';}
applyTheme();themeButton.addEventListener('click',()=>{themeChanged=true;theme=theme==='dark'?'light':'dark';applyTheme();});systemTheme.addEventListener('change',()=>{if(!themeChanged){theme=systemTheme.matches?'dark':'light';applyTheme();}});

const memoryPhoto=document.querySelector('#memory-photo'),memoryLink=document.querySelector('#memory-link'),memoryPlace=document.querySelector('#memory-place'),memoryMap=document.querySelector('#memory-map');
let memoryIndex=0,memoryRun=0;
async function showMemory(step){memoryIndex=(memoryIndex+step+memories.length)%memories.length;const item=memories[memoryIndex],token=++memoryRun;const preload=new Image();preload.src=item.src;try{await preload.decode();if(token!==memoryRun)return;memoryPhoto.src=item.src;memoryPhoto.alt=item.alt;memoryPhoto.width=preload.naturalWidth;memoryPhoto.height=preload.naturalHeight;memoryLink.href=item.url;memoryLink.setAttribute('aria-label','Tecirc Memory / '+item.place);memoryPlace.textContent=item.place;memoryMap.setAttribute('aria-label','おおよその撮影地：'+item.place);for(const id of ['map-ring','map-point']){const marker=document.querySelector('#'+id);marker.setAttribute('cx',String(item.lon+180));marker.setAttribute('cy',String(90-item.lat));}document.querySelector('#memory-status').textContent=(memoryIndex+1)+' / '+memories.length;syncMemoryIndex();warmMemories();}catch{if(token===memoryRun)document.querySelector('#memory-status').textContent=language==='jp'?'写真を読み込めませんでした。もう一度お試しください。':'Photo unavailable. Please try again.';}}
document.querySelector('#memory-prev').addEventListener('click',()=>showMemory(-1));document.querySelector('#memory-next').addEventListener('click',()=>showMemory(1));

function warmMemories(){for(const offset of [-1,1]){const item=memories[(memoryIndex+offset+memories.length)%memories.length];const image=new Image();image.src=item.src;}}
warmMemories();
document.querySelector('.photo-card').addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();showMemory(e.key==='ArrowRight'?1:-1);}});

const memoryIndexHost=document.querySelector('#memory-index');
for(const [index,item] of memories.entries()){const button=document.createElement('button');button.type='button';button.className='memory-item';button.setAttribute('aria-label',`${index+1}: ${item.place}`);button.setAttribute('aria-current',String(index===0));const thumb=document.createElement('img');thumb.src=`./assets/memory-thumb-${String(index+1).padStart(2,'0')}.webp`;thumb.alt='';thumb.width=240;thumb.height=160;thumb.loading='lazy';thumb.decoding='async';const label=document.createElement('span');const place=document.createElement('span');place.textContent=item.place;const number=document.createElement('b');number.textContent=String(index+1).padStart(2,'0');label.append(place,number);button.append(thumb,label);button.addEventListener('click',()=>{setView('memory');showMemory(index-memoryIndex);});memoryIndexHost.append(button);}
function syncMemoryIndex(){document.querySelectorAll('.memory-item').forEach((button,index)=>button.setAttribute('aria-current',String(index===memoryIndex)));const item=memories[memoryIndex];document.querySelector('#memory-coordinates').textContent=`${Math.abs(item.lat).toFixed(2)}° ${item.lat>=0?'N':'S'} / ${Math.abs(item.lon).toFixed(2)}° ${item.lon>=0?'E':'W'}`;document.querySelector('#photo-position').textContent=String(memoryIndex+1).padStart(2,'0')+' / '+memories.length;}
function applyView(){const view=location.hash==='#memory'?'memory':'about';document.body.classList.toggle('view-memory',view==='memory');document.querySelector('#view-path').textContent='~/4k29/'+view;document.querySelectorAll('[data-view]').forEach(link=>{if(link.dataset.view===view)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});}
function setView(view){if(location.hash!=='#'+view)history.pushState(null,'','#'+view);applyView();if(view==='about')animateProfileCode();}
window.addEventListener('hashchange',()=>{applyView();if(location.hash!=='#memory')animateProfileCode();});applyView();syncMemoryIndex();

const profileCode=document.querySelector('#profile-code');
const codeTokens=[['code-keyword','const '],['','shika'],['code-punctuation',' = '],['code-string','"4k29"'],['code-punctuation',';\n'],['code-keyword','const '],['','journal'],['code-punctuation',' = '],['code-string','"Tecirc"'],['code-punctuation',';\n'],['code-keyword','const '],['','memories'],['code-punctuation',' = '],['code-number',String(memories.length)],['code-punctuation',';']];
let codeRun=0;
async function animateProfileCode(){const run=++codeRun;profileCode.replaceChildren();profileCode.parentElement.classList.add('is-typing');for(const [className,token] of codeTokens){if(run!==codeRun)return;const span=document.createElement('span');span.className=className;profileCode.append(span);for(const letter of token){if(run!==codeRun)return;span.textContent+=letter;if(!reduced.matches)await pause(22);}}if(run===codeRun)profileCode.parentElement.classList.remove('is-typing');}
document.querySelectorAll('[data-view]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();setView(link.dataset.view);}));
new IntersectionObserver((entries,observer)=>{if(entries.some(entry=>entry.isIntersecting)){animateProfileCode();observer.disconnect();}},{threshold:.5}).observe(profileCode);
