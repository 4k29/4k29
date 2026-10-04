const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const base=process.env.SITE_URL||'http://localhost:8001/';
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE});
 for(const mobile of [false,true]){
  const context=await browser.newContext({reducedMotion:'reduce',isMobile:mobile,hasTouch:mobile,viewport:mobile?{width:390,height:844}:{width:1440,height:900}});
  const page=await context.newPage(),errors=[],remote=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(base))remote.push(r.url());});
  await page.goto(base);await page.waitForFunction(()=>!document.querySelector('#prompt-form button').disabled);
  let count=0;
  async function ask(q){
   await page.locator('#prompt-input').fill(q);await page.locator('#prompt-input').press('Enter');count++;
   await page.waitForFunction(n=>document.querySelectorAll('.chat-response').length===n&&document.querySelector('#chat').getAttribute('aria-busy')==='false',count);
   const row=page.locator('.chat-response').nth(count-1);assert.doesNotMatch(await row.innerText(),/と述べ|挙げています|本人は|プロフィールに/);return row;
  }
  let row=await ask('好きなドラマは？');assert.match(await row.innerText(),/VIVANT/);assert.match(await row.innerText(),/TOKYO MER/);assert.deepEqual(new Set(await row.locator('a').evaluateAll(items=>items.map(a=>a.href))),new Set(['https://www.tbs.co.jp/VIVANT_tbs/about/','https://www.tbs.co.jp/TokyoMER_tbs/about/']));
  row=await ask('kyuについて教えて');assert.match(await row.innerText(),/カメラとアプリ/);assert.match(await row.innerText(),/機能を意図的に絞/);assert.equal(await row.locator('a').first().getAttribute('href'),'https://kyu-core.com/');
  row=await ask('VIVANTの内容は？');assert.match(await row.innerText(),/商社マン/);
  row=await ask('もっと詳しく');assert.match(await row.innerText(),/乃木憂助/);
  row=await ask('名前だけ');assert.equal(await row.innerText(),'VIVANT');assert.equal(await row.locator('a').count(),0);
  for(const q of ['イヤホンは？','ヘッドホンは？']){row=await ask(q);const text=await row.innerText();for(const value of ['イヤホン','ヘッドホン','Beats Fit Pro','CMF Buds','Nothing Headphone (1)'])assert.ok(text.includes(value),value);}
  row=await ask('kyuのカメラ持ってる？');assert.equal(await row.innerText(),'すみません、よく分かりません');
  await page.evaluate(()=>document.fonts.ready);
  const font=await page.locator('#prompt-input').evaluate(el=>getComputedStyle(el).fontFamily);assert.match(font,/Noto Sans JP/);
  assert.ok(await page.evaluate(()=>[...document.fonts].some(f=>f.family==='Noto Sans JP'&&f.status==='loaded')));
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
  await page.screenshot({path:`/tmp/4k29-favorites-${mobile?'mobile':'desktop'}.png`,fullPage:true});
  console.log(`PASS ${mobile?'mobile':'desktop'}: researched favorite descriptions, first-person voice, context, scoped links, unified audio, Japanese font`);
  await context.close();
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
