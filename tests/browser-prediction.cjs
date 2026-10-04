const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const base=process.env.SITE_URL||'http://localhost:8001/';
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE});
 for(const mobile of [false,true]){
  const context=await browser.newContext({reducedMotion:'reduce',isMobile:mobile,hasTouch:mobile,viewport:mobile?{width:390,height:844}:{width:1440,height:900}});
  const page=await context.newPage(),errors=[],remote=[],modules=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(base))remote.push(r.url());if(/\.js\?/.test(r.url()))modules.push(r.url());});
  let count=0;
  async function ready(){await page.waitForFunction(()=>!document.querySelector('#prompt-form button').disabled);count=0;}
  async function ask(q){
   await page.locator('#prompt-input').fill(q);await page.locator('#prompt-input').press('Enter');count++;
   await page.waitForFunction(n=>document.querySelectorAll('.chat-response').length===n&&document.querySelector('#chat').getAttribute('aria-busy')==='false',count);
   return page.locator('.chat-response').nth(count-1);
  }
  const records=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('4k29.question-journal.v1')).records);
  await page.goto(base);await ready();
  const names=[];for(let i=0;i<10;i++){const row=await ask('名前は？');names.push(await row.innerText());}
  assert.ok(new Set(names).size>=8);assert.ok(names.every(t=>t.includes('4k29')&&!/だよ。|いるよ。/.test(t)));
  await ask('これからは丁寧な口調で短く答えて');
  assert.deepEqual((await records()).at(-1).preferenceUpdate,{style:'polite',length:'brief'});
  let row=await ask('名前は？');assert.match(await row.innerText(),/です|ます|ください/);
  await page.reload();await ready();row=await ask('名前は？');assert.match(await row.innerText(),/です|ます|ください/);
  await ask('好きな人は？');row=await ask('その人のYouTubeのリンクだけ');assert.equal(await row.locator('a').count(),1);assert.equal(await row.locator('a').getAttribute('href'),'https://m.youtube.com/@shiteharu?ra=m');
  row=await ask('くだけた口調でヘッドホンの価格を教えて');assert.equal(await row.innerText(),'すみません、よく分かりません');assert.equal((await records()).at(-1).preferenceUpdate,null);
  await page.evaluate(()=>localStorage.removeItem('4k29.question-journal.v1'));await page.reload();await ready();
  row=await ask('名前は？');assert.match(await row.innerText(),/4k29/);assert.doesNotMatch(await row.innerText(),/だよ。/);
  row=await ask('記事で扱う話題を教えてもらえる？');assert.match(await row.innerText(),/記事|テーマ/);
  assert.ok(modules.some(url=>url.includes('neural-model.js?v=20261004-transformer-7')));
  assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  console.log(`PASS ${mobile?'mobile':'desktop'}: predictive model loads, 8+ grounded variations, preference persistence/reset, scoped links, unknowns, no external requests`);
  await context.close();
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
