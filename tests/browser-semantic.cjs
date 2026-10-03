const {chromium}=require('playwright');const assert=require('node:assert/strict');
const base=process.env.SITE_URL||'http://localhost:8001/';
(async()=>{const b=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{}),...(process.env.USE_PROXY?{proxy:{server:process.env.HTTPS_PROXY}}:{})});
const p=await b.newPage({reducedMotion:'reduce'}),errors=[],remote=[];p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(!r.url().startsWith(base))remote.push(r.url());});await p.goto(base);await p.waitForFunction(()=>!document.querySelector('#prompt-form button').disabled);
let n=0;async function ask(q){await p.locator('#prompt-input').fill(q);await p.locator('#prompt-input').press('Enter');n++;await p.waitForFunction(n=>document.querySelectorAll('.chat-response').length===n&&document.querySelector('#chat').getAttribute('aria-busy')==='false',n);return p.locator('.chat-response').nth(n-1);}
let a=await ask('あなた誰？');assert.match(await a.innerText(),/4k29/);a=await ask('AIに全部任せてるの？自分では何をしてる？');assert.match(await a.innerText(),/ChatGPT/);assert.match(await a.innerText(),/アイデア/);assert.doesNotMatch(await a.innerText(),/よく分かりません/);
a=await ask('制作の流れを具体的に説明して');assert.match(await a.innerText(),/プロンプト.*プレビュー.*改善/);
a=await ask('あなたについて簡単に教えて');assert.match(await a.innerText(),/4k29/);assert.match(await a.innerText(),/学生/);
a=await ask('私の名前は？');assert.equal(await a.innerText(),'すみません、よく分かりません');a=await ask('記事は何処で読める？');assert.equal(await a.locator('a').getAttribute('href'),'https://4k29.github.io/tecirc/');a=await ask('なんのいやほんつかってる');assert.match(await a.innerText(),/Beats Fit Pro/);assert.match(await a.innerText(),/CMF Buds/);assert.doesNotMatch(await a.innerText(),/Headphone/);
a=await ask('けいやくしてるさぶすくは');assert.match(await a.innerText(),/ChatGPT Plus/);assert.match(await a.innerText(),/Apple One/);assert.match(await a.innerText(),/250GB/);assert.doesNotMatch(await a.innerText(),/uma_4k/);
a=await ask('おしはだれ');assert.match(await a.innerText(),/してはる/);
a=await ask('サブ垢は？');assert.equal(await a.locator('a').getAttribute('href'),'https://x.com/uma_4k');
assert.equal(await p.locator('.chat-disclaimer').count(),0);
assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);console.log('PASS real chat: who/identity, AI-human division, workflow, brief answer, unknown visitor identity, article link; no external requests');await b.close();})().catch(e=>{console.error(e);process.exit(1)});
