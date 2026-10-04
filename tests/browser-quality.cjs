const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const base=process.env.SITE_URL||'http://localhost:8001/';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
 for(const mobile of [false,true]){
  const context=await browser.newContext({reducedMotion:'reduce',viewport:mobile?{width:390,height:844}:{width:1440,height:900}});
  const page=await context.newPage(),errors=[],remote=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(base))remote.push(r.url());});
  await page.goto(base);await page.waitForFunction(()=>!document.querySelector('#prompt-form button').disabled);
  let count=0;
  async function ask(question){
   await page.locator('#prompt-input').fill(question);await page.locator('#prompt-input').press('Enter');count++;
   await page.waitForFunction(n=>document.querySelectorAll('.chat-response').length===n&&document.querySelector('#chat').getAttribute('aria-busy')==='false',count);
   return page.locator('.chat-response').nth(count-1);
  }
  let row=await ask('イヤホンとヘッドホンは？');let text=await row.innerText();
  for(const word of ['イヤホン','ヘッドホン','Beats Fit Pro','CMF Buds','Nothing Headphone (1)'])assert.ok(text.includes(word));
  row=await ask('ランニング用の靴とアプリは何？');text=await row.innerText();assert.match(text,/ペガサス|Pegasus/i);assert.match(text,/Nike Run Club/);
  row=await ask('イヤホンの機種と値段は？');text=await row.innerText();assert.match(text,/Beats Fit Pro/);assert.match(text,/料金・価格については、まだ答えられません/);
  row=await ask('好きな分野だけ教えて');text=await row.innerText();assert.match(text,/UI・UX/);assert.doesNotMatch(text,/Apple|Nothing|OpenAI/);
  row=await ask('推しのYouTubeとあなたのXを教えて');
  assert.deepEqual((await row.locator('a').evaluateAll(links=>links.map(l=>l.href))).sort(),['https://m.youtube.com/@shiteharu?ra=m','https://x.com/p_horeer','https://x.com/uma_4k'].sort());
  row=await ask('推しのYouTubeと推しのXは？');assert.equal(await row.locator('a').count(),2);
  row=await ask('その人のXは？');assert.equal(await row.locator('a').count(),1);assert.equal(await row.locator('a').getAttribute('href'),'https://x.com/popico_pi');
  row=await ask('その人のYouTubeのチャンネルは？');assert.equal(await row.locator('a').count(),1);assert.equal(await row.locator('a').getAttribute('href'),'https://m.youtube.com/@shiteharu?ra=m');
  await ask('サブスクは？');row=await ask('名前だけ教えて');text=await row.innerText();assert.match(text,/ChatGPT Plus/);assert.doesNotMatch(text,/4k29|サブスクとして|契約/);
  await ask('ランニングは？');row=await ask('アプリは？');assert.match(await row.innerText(),/Nike Run Club/);
  row=await ask('ヘッドホンはどこで買った？');assert.equal(await row.innerText(),'すみません、よく分かりません');
  row=await ask('アプリは？');assert.equal(await row.innerText(),'すみません、よく分かりません');
  assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  console.log(`PASS ${mobile?'mobile':'desktop'}: compound answers, scoped links, contextual follow-ups, unsupported attributes, no external requests`);
  await context.close();
 }
 await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});
