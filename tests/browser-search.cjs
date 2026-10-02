const {chromium}=require('playwright');const assert=require('node:assert/strict');
const base=process.env.SITE_URL||'http://localhost:8001/';
const fixture={timezone:'Asia/Tokyo',current:{time:'2026-10-02T22:00',weather_code:1,temperature_2m:18.2},daily:{time:['2026-10-02','2026-10-03','2026-10-04'],weather_code:[61,3,0],temperature_2m_max:[22,23,24],temperature_2m_min:[17,18,19],precipitation_probability_max:[80,30,0]}};
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{}),...(process.env.USE_PROXY?{proxy:{server:process.env.HTTPS_PROXY,bypass:'localhost,127.0.0.1'}}:{})});
 for(const mobile of [false,true])for(const scheme of ['dark','light']){
  const ctx=await browser.newContext({viewport:mobile?{width:390,height:844}:{width:1440,height:900},colorScheme:scheme,reducedMotion:'reduce',geolocation:{latitude:35.6895123,longitude:139.6917123}});
  await ctx.addInitScript(()=>{window.locationReads=0;const original=navigator.geolocation.getCurrentPosition.bind(navigator.geolocation);navigator.geolocation.getCurrentPosition=(...args)=>{window.locationReads++;return original(...args);};});
  const api=[],errors=[],remote=[];const p=await ctx.newPage();p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(!r.url().startsWith(base))remote.push(r.url());});
  await ctx.route('https://geocoding-api.open-meteo.com/**',async route=>{
   const url=new URL(route.request().url());api.push(url);assert.equal(url.searchParams.has('history'),false);assert.equal(route.request().headers().referer,undefined);
   const name=url.searchParams.get('name');const results=name==='Unknown'?[]:name==='Paris'?[{name:'Paris',latitude:48.85,longitude:2.35,country:'フランス',admin1:'イル・ド・フランス'},{name:'Paris',latitude:33.66,longitude:-95.55,country:'アメリカ',admin1:'テキサス'}]:[{name:'東京都',latitude:35.68,longitude:139.69,country_code:'JP',country:'日本'}];
   await route.fulfill({json:{results},headers:{'Access-Control-Allow-Origin':'*'}});
  });
  await ctx.route('https://api.open-meteo.com/**',async route=>{const url=new URL(route.request().url());api.push(url);assert.equal(route.request().headers().referer,undefined);if(url.searchParams.get('latitude')==='33.66')await route.abort();else await route.fulfill({json:fixture,headers:{'Access-Control-Allow-Origin':'*'}});});
  await p.goto(base);await p.locator('#boot-next:enabled').click();await p.locator('.transition-next').click();await p.waitForFunction(()=>!document.querySelector('#prompt-form button').disabled);
  let n=0;async function wait(){await p.waitForFunction(n=>document.querySelectorAll('.chat-response').length===n&&document.querySelector('#chat').getAttribute('aria-busy')==='false',n);return p.locator('.chat-response').nth(n-1);}
  async function ask(q){await p.locator('#prompt-input').fill(q);await p.locator('#prompt-input').press('Enter');n++;return wait();}
  let a=await ask('あなた誰？');assert.match(await a.innerText(),/4k29/);assert.equal(api.length,0);
  a=await ask('今日の天気は？');assert.match(await a.innerText(),/どこの天気/);assert.equal(api.length,0);assert.equal(await p.evaluate(()=>window.locationReads),0);
  a=await ask('サブ垢は？');assert.equal(await a.locator('a').getAttribute('href'),'https://x.com/uma_4k');assert.equal(api.length,0);
  a=await ask('とうきょうのあしたのてんき');assert.match(await a.innerText(),/明日（2026-10-03）/);assert.match(await a.innerText(),/23°C/);assert.match(await a.innerText(),/30%/);assert.equal(api[0].searchParams.get('name'),'Tokyo');assert.equal(await a.getByRole('link',{name:'Open-Meteo',exact:true}).getAttribute('href'),'https://open-meteo.com/');
  a=await ask('明後日は？');assert.match(await a.innerText(),/明後日（2026-10-04）/);assert.match(await a.innerText(),/24°C/);assert.equal(api.length,3);
  const before=api.length;a=await ask('今日のニュースは？');assert.match(await a.innerText(),/最新情報は検索先/);assert.equal(api.length,before);const google=a.getByRole('link',{name:'Googleで検索',exact:true});assert.equal(new URL(await google.getAttribute('href')).hostname,'www.google.com');assert.equal(await google.getAttribute('target'),'_blank');assert.equal(await google.getAttribute('rel'),'noopener noreferrer');
  await p.locator('#search-toggle').click();assert.equal(await p.locator('#search-toggle').getAttribute('aria-pressed'),'true');a=await ask('OpenAIとは？');assert.match(await a.innerText(),/Google検索/);assert.equal(api.length,before);await p.locator('#search-toggle').click();a=await ask('イヤホンは？');assert.match(await a.innerText(),/Beats Fit Pro/);assert.equal(api.length,before);
  a=await ask('Parisの天気');assert.equal(await a.locator('button').count(),2);assert.doesNotMatch(await a.innerText(),/最高/);await a.getByRole('button',{name:/アメリカ/}).click();n++;a=await wait();assert.match(await a.innerText(),/取得できませんでした/);assert.equal(await a.locator('a').count(),1);
  a=await ask('現在地の天気');assert.equal(await p.evaluate(()=>window.locationReads),0);await ctx.grantPermissions(['geolocation']);await a.getByRole('button',{name:'現在地を使う'}).click();n++;a=await wait();assert.match(await a.innerText(),/現在地付近/);assert.equal(await p.evaluate(()=>window.locationReads),1);assert.equal(api.at(-1).searchParams.get('latitude'),'35.69');
  a=await ask('Unknownの天気');assert.match(await a.innerText(),/地域が見つかりません/);a=await ask('検索: <img src=x onerror=alert(1)>');assert.equal(await a.locator('img').count(),0);assert.match(await a.innerText(),/<img/);
  assert.equal(await p.locator('.search-privacy').isVisible(),true);assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);assert.ok(remote.every(url=>['api.open-meteo.com','geocoding-api.open-meteo.com'].includes(new URL(url).hostname)),remote.join('\n'));
  await p.screenshot({path:`/tmp/search-${mobile?'mobile':'desktop'}-${scheme}.png`,fullPage:true});console.log(`PASS ${mobile?'mobile':'desktop'} ${scheme}: local privacy, weather/day/context, ambiguity, Google only, failures, explicit geolocation, XSS, no overflow`);await ctx.close();
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
