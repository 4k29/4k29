const {chromium}=require('playwright');const assert=require('node:assert/strict');
const base=process.env.SITE_URL||'http://localhost:8001/';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{}),...(process.env.USE_PROXY?{proxy:{server:process.env.HTTPS_PROXY,bypass:'localhost,127.0.0.1'}}:{})});
 const p=await browser.newPage({reducedMotion:'reduce'}),errors=[],apis=[];p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(/(?:geocoding-api|api)\.open-meteo\.com/.test(r.url()))apis.push({url:r.url(),status:r.status()});});
 await p.goto(base);await p.locator('#boot-next:enabled').click();await p.locator('.transition-next').click();await p.waitForFunction(()=>!document.querySelector('#prompt-form button').disabled);
 await p.locator('#prompt-input').fill('東京の今日の天気は？');await p.locator('#prompt-input').press('Enter');await p.waitForFunction(()=>document.querySelector('.chat-response')&&document.querySelector('#chat').getAttribute('aria-busy')==='false');
 const text=await p.locator('.chat-response').innerText();assert.match(text,/東京都/);assert.match(text,/今日（\d{4}-\d{2}-\d{2}）/);assert.match(text,/最高 -?\d/);assert.match(text,/降水確率/);assert.match(text,/出典：Open-Meteo/);assert.equal(apis.length,2);assert.ok(apis.every(r=>r.status===200));assert.deepEqual(errors,[]);
 await p.locator('#prompt-input').fill('OpenAIを検索して');await p.locator('#prompt-input').press('Enter');await p.waitForFunction(()=>document.querySelectorAll('.chat-response').length===2&&document.querySelector('#chat').getAttribute('aria-busy')==='false');const link=p.locator('.chat-response').nth(1).getByRole('link',{name:'Googleで検索'});assert.equal(new URL(await link.getAttribute('href')).searchParams.get('q'),'OpenAI');
 console.log('PASS real Open-Meteo geocoding + forecast, browser CORS, dated weather, provenance and Google search URL');console.log(text);await p.screenshot({path:'/tmp/weather-live.png',fullPage:true});await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
