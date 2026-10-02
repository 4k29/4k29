import test from 'node:test';
import assert from 'node:assert/strict';
import {deviceInfo,collectDeviceInfo} from '../docs/device-info.js';
const screen={width:390,height:844},viewport={innerWidth:390,innerHeight:700};
const report=(userAgent,other={})=>deviceInfo({userAgent,...other},screen,viewport);
test('Safari and Firefox identify explicit desktop and iOS identifiers without Client Hints',()=>{
 const cases=[
  ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Safari/605.1.15','macOS','Safari 18.4'],
  ['Mozilla/5.0 (iPhone; CPU iPhone OS 18_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Mobile/15E148 Safari/604.1','iOS','Safari 18.4'],
  ['Mozilla/5.0 (iPad; CPU OS 18_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Mobile/15E148 Safari/604.1','iPadOS','Safari 18.4'],
  ['Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0','Windows','Firefox 144.0'],
  ['Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0','Linux','Firefox 144.0']
 ];
 for(const [ua,os,browser] of cases){const result=report(ua);assert.equal(result.OS,os);assert.equal(result.Browser,browser);}
 assert.equal(report(cases[1][0]).Device,'iPhone');assert.equal(report(cases[2][0]).Device,'iPad');
});
test('browser variants take precedence over compatibility Chrome and Safari tokens',()=>{
 const base='Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Mobile Safari/537.36';
 for(const [suffix,expected] of [[' EdgA/153.0.0.0','Edge'],[' SamsungBrowser/28.0','Samsung Internet'],[' OPR/90.0','Opera'],['','Chrome']]){
  const result=report(base+suffix);assert.equal(result.OS,'Android');assert.ok(result.Browser.startsWith(expected));assert.equal(result.Device,'Mobile (browser-reported)');
 }
 for(const [token,name] of [['CriOS','Chrome'],['FxiOS','Firefox'],['EdgiOS','Edge']])assert.ok(report(`Mozilla/5.0 (iPhone; CPU iPhone OS 18_4 like Mac OS X) AppleWebKit/605.1.15 ${token}/153.0 Mobile/15E148 Safari/604.1`).Browser.startsWith(name));
});
test('Client Hints supply exposed full versions and model, filtering grease brands',async()=>{
 const nav={userAgentData:{platform:'Android',mobile:true,brands:[{brand:'Not(A:Brand',version:'99'},{brand:'Chromium',version:'153'},{brand:'Google Chrome',version:'153'}],getHighEntropyValues:async()=>({platformVersion:'15.0.0',fullVersionList:[{brand:'Chromium',version:'153.0.1.2'},{brand:'Google Chrome',version:'153.0.1.2'}],model:'Pixel 9',formFactors:['Mobile']})}};
 const result=await collectDeviceInfo(nav,screen,viewport);assert.equal(result.OS,'Android');assert.equal(result['OS version'],'15.0.0');assert.equal(result.Browser,'Chrome 153.0.1.2');assert.equal(result.Model,'Pixel 9');assert.equal(result.Device,'Mobile');
});
test('denied or stalled capabilities fall back without blocking the boot',async()=>{
 const nav={userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153.0.0.0 Safari/537.36',userAgentData:{getHighEntropyValues:async()=>{throw Error('denied');}}};
 assert.equal((await collectDeviceInfo(nav,screen,viewport)).OS,'Windows');
 nav.userAgentData.getHighEntropyValues=()=>new Promise(()=>{});
 assert.equal((await collectDeviceInfo(nav,screen,viewport)).Browser,'Chrome 153.0.0.0');
});
test('masked or absent details are not invented',()=>{
 const desktopMac='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.4 Safari/605.1.15';
 assert.equal(report(desktopMac,{maxTouchPoints:5}).Device,'Unknown (desktop identity; touch-capable)');assert.equal(report(desktopMac,{maxTouchPoints:5}).OS,'Unknown (browser reports macOS)');
 const windows=report('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153.0.0.0 Safari/537.36');assert.equal(windows['OS version'],'Unknown');assert.equal(windows.Model,'Unknown');
 const empty=deviceInfo({}, {}, {});for(const value of Object.values(empty))assert.equal(value,'Unknown');
 assert.equal(report('',{platform:'MacIntel'}).OS,'macOS');
});

test('Windows Client Hints contracts identify 10 and 11 without treating them as release numbers',()=>{
 const nav={userAgentData:{platform:'Windows',mobile:false}};
 const win11=deviceInfo(nav,screen,viewport,{platformVersion:'13.0.0'});assert.equal(win11.OS,'Windows 11');assert.equal(win11['OS version'],'11');assert.equal(win11['Platform version'],'13.0.0');
 const win10=deviceInfo(nav,screen,viewport,{platformVersion:'10.0.0'});assert.equal(win10.OS,'Windows 10');assert.equal(win10['OS version'],'10');
 assert.equal(deviceInfo(nav,screen,viewport,{}).OS,'Windows');
});
