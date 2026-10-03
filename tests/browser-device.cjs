const {chromium,firefox}=require('playwright');const assert=require('node:assert/strict');
const base=process.env.SITE_URL||'http://localhost:8001/';
(async()=>{
 for(const [name,engine] of [['chromium',chromium],['firefox',firefox]]){
  const options={headless:true};if(name==='chromium'&&process.env.BROWSER_EXECUTABLE)options.executablePath=process.env.BROWSER_EXECUTABLE;
  const browser=await engine.launch(options),page=await browser.newPage({reducedMotion:'reduce'});await page.goto(base);await page.locator('.transition-next').click();await page.waitForFunction(()=>document.querySelector('#boot-log').textContent.includes('[ready]'));await page.locator('#device-summary').click();const log=await page.locator('#boot-log').innerText();assert.match(log,/OS: Linux/);assert.match(log,/Browser: (Chromium|Chrome|Firefox)/);await page.waitForFunction(()=>!document.querySelector('#prompt-form button').disabled);console.log(`PASS ${name}: actual browser-reported OS and browser`);await browser.close();
 }
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
 const cases=[
  ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.4 Safari/605.1.15','macOS','Safari'],
  ['Mozilla/5.0 (iPhone; CPU iPhone OS 18_4 like Mac OS X) AppleWebKit/605.1.15 Version/18.4 Mobile/15E148 Safari/604.1','iOS','Safari'],
  ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0','Windows','Edge']
 ];
 for(const [userAgent,os,name] of cases){
  const context=await browser.newContext({userAgent,reducedMotion:'reduce'});await context.addInitScript(()=>Object.defineProperty(Navigator.prototype,'userAgentData',{get:()=>undefined}));const page=await context.newPage();await page.goto(base);await page.locator('.transition-next').click();await page.waitForFunction(()=>document.querySelector('#boot-log').textContent.includes('[ready]'));await page.locator('#device-summary').click();const log=await page.locator('#boot-log').innerText();assert.ok(log.includes('OS: '+os));assert.ok(log.includes('Browser: '+name));console.log(`PASS identifier fixture ${os}/${name}: boot DOM fallback without Client Hints`);await context.close();
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
