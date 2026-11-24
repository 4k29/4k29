import { profile, photos, articles, projects } from './content.js';
import { box, bottomRight, clamp, corner, cursor, drawFrame, ease, mixBox, mixPoint, phase, place, point, right, hash, Scramble, visible } from './motion.js';

const byId = (id) => document.getElementById(id);
const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [name,value] of Object.entries(attrs)) {
    if (value !== undefined) node.setAttribute(name, value);
  }
  node.append(...children);
  return node;
};
const link = (text,url) => el('a',{class:'inline-link',href:url,target:'_blank',rel:'noopener noreferrer'},text);
function image(source,alt,pictureClass) {
  const img = el('img',{src:source,alt,decoding:'async',class:pictureClass});
  img.addEventListener('error',()=>{
    img.hidden = true;
    if (img.parentElement && !img.parentElement.querySelector('.media-fallback')) {
      img.after(el('span',{class:'media-fallback','aria-hidden':'true'},'Image unavailable'));
    }
  },{once:true});
  return img;
}
function profileLinks(target) {
  for (const item of profile.links) target.append(link(item.label,item.url));
}
function aboutContent(target) {
  target.append(
    el('h2',{'data-scramble':''},profile.heading),
    el('div',{'data-after-title':''},el('p',{},profile.bio),
      el('ul',{class:'tags'},...profile.interests.map(tag=>el('li',{},tag)))),
  );
}
function projectContent(item) {
  const visual = el('div',{class:'project-visual'});
  visual.append(item.image ? artwork(item,'project-image') : el('span',{class:'project-symbol'},item.title));
  return el('div',{class:'project-body'},visual,
    el('div',{class:'project-copy'},el('h2',{'data-scramble':''},item.title),
      el('div',{'data-after-title':''},el('p',{},item.description),link(item.linkLabel || 'View project',item.url))));
}
function artwork(item,className) {
  return el('div',{class:`artwork ${className}`},image(item.image,item.alt || ''));
}
function articleLink(item) {
  const anchor=link(item.title,item.url);
  anchor.lang='ja';
  return anchor;
}
const experience = byId('experience');
const stage = byId('stage');
const scrollHint = byId('scroll-hint');
const frame = byId('frame');
const intro = byId('intro');
const about = byId('about');
const projectPanel = byId('project-panel');
const contact = byId('contact');
const agent = byId('agent');
aboutContent(about.querySelector('.about-content'));
profileLinks(contact.querySelector('.profile-links'));

const projectNodes = projects.map(item=>{
  const node = el('div',{class:'project-item',hidden:''},projectContent(item));
  projectPanel.append(node);
  return node;
});
function framePoint(region,x,y) {
  const angle=region.rotation*Math.PI/180;
  return point(region.x+x*Math.cos(angle)-y*Math.sin(angle),
    region.y+x*Math.sin(angle)+y*Math.cos(angle));
}

function pushAside(region, obstacle, {W,H}) {
  const gap=6;
  const left=obstacle.x-gap-region.w;
  const right=obstacle.x+obstacle.w+gap;
  const top=obstacle.y-gap-region.h;
  const bottom=obstacle.y+obstacle.h+gap;
  if(region.x<=left || region.x>=right || region.y<=top || region.y>=bottom) return region;
  const bound=(value,max)=>Math.max(5,Math.min(max,value));
  const options=[
    [left,region.y],[right,region.y],[region.x,top],[region.x,bottom],
  ].map(([x,y])=>[bound(x,W-5-region.w),bound(y,H-5-region.h)]);
  const score=([x,y])=>{
    const overlapX=Math.max(0,Math.min(x+region.w,obstacle.x+obstacle.w)-Math.max(x,obstacle.x));
    const overlapY=Math.max(0,Math.min(y+region.h,obstacle.y+obstacle.h)-Math.max(y,obstacle.y));
    return overlapX*overlapY*4+Math.hypot(x-region.x,y-region.y);
  };
  const [x,y]=options.reduce((best,candidate)=>score(candidate)<score(best) ? candidate : best);
  return box(x,y,region.w,region.h,region.rotation);
}

function createGallery(id,items,article=false) {
  const gallery=byId(id);
  const heading=gallery.querySelector('h2');
  const headingText=new Scramble(heading);
  const seed=Math.floor(Math.random()*32768);
  const variation=(index,channel)=>hash(seed+index*397+channel*883);
  const close=el('button',{class:'text-button gallery-close',type:'button',hidden:''},'Back to grid');
  const detail=el('div',{class:'gallery-detail',hidden:''});
  const photoName=el('span',{class:'gallery-filename'});
  const articleTitle=article ? articleLink(items[0]) : null;
  const caption=articleTitle ?? photoName;
  detail.append(caption);
  const tiles=items.map((item,index)=>{
    const visual=artwork(item,'gallery-image');
    const titlebar=el('span',{class:'gallery-titlebar','aria-hidden':'true'},item.title);
    const button=el('button',{
      class:'gallery-tile',type:'button','aria-label':item.title,'aria-pressed':'false',title:item.title,
    },titlebar,visual);
    button.addEventListener('click',event=>{
      if(event.detail && ignoreClick===index) { ignoreClick=-1; return; }
      select(selected===index ? -1 : index);
    });
    button.addEventListener('pointerdown',event=>beginDrag(event,index));
    gallery.append(button);
    return {item,button};
  });
  gallery.append(close,detail);

  let selected=-1, regions, resting, movement, afterClose, drag, ignoreClick=-1;
  function beginDrag(event,index) {
    if(!event.isPrimary || event.button!==0 || !event.target.closest('.gallery-titlebar') || gallery.inert || movement) return;
    ignoreClick=-1;
    drag={index,id:event.pointerId,x:event.clientX,y:event.clientY,from:regions,lastX:event.clientX,lastY:event.clientY,lastTime:event.timeStamp,vx:0,vy:0};
    tiles[index].button.setPointerCapture(event.pointerId);
  }
  gallery.addEventListener('pointermove',event=>{
    if(drag?.id!==event.pointerId) return;
    const dx=event.clientX-drag.x, dy=event.clientY-drag.y;
    if(!drag.moved && Math.hypot(dx,dy)<6) return;
    drag.moved=true;
    const dt=event.timeStamp-drag.lastTime;
    if(dt>0) {
      drag.vx=(event.clientX-drag.lastX)/dt;
      drag.vy=(event.clientY-drag.lastY)/dt;
      drag.lastX=event.clientX;
      drag.lastY=event.clientY;
      drag.lastTime=event.timeStamp;
    }
    const origin=drag.from[drag.index];
    const x=Math.max(5,Math.min(metrics.W-origin.w-5,origin.x+dx));
    const y=Math.max(5,Math.min(metrics.H-origin.h-5,origin.y+dy));
    const card=box(x,y,origin.w,origin.h);
    regions=regions.map((region,i)=>i===drag.index ? card : pushAside(region,card,metrics));
    requestRender();
  });
  function endDrag(event) {
    if(drag?.id!==event.pointerId) return;
    const {index,moved,vx,vy,lastTime}=drag;
    drag=undefined;
    if(!moved) return;
    ignoreClick=index;
    const from=regions;
    const landed=from[index];
    const coast=event.type==='pointerup' && event.timeStamp-lastTime<85 ? 95 : 0;
    const offset=value=>Math.max(-100,Math.min(100,value*coast));
    const target=box(Math.max(5,Math.min(metrics.W-landed.w-5,landed.x+offset(vx))),
      Math.max(5,Math.min(metrics.H-landed.h-5,landed.y+offset(vy))),landed.w,landed.h);
    if(!coast || reduced.matches) {
      if(selected<0) resting=regions;
      return;
    }
    const to=from.map((region,i)=>i===index ? target : pushAside(region,target,metrics));
    if(selected<0) resting=to;
    movement={from,to,index,throwing:true};
    gallery.setAttribute('aria-busy','true');
    requestRender();
  }
  gallery.addEventListener('pointerup',endDrag);
  gallery.addEventListener('pointercancel',endDrag);
  function select(index) {
    if(index===selected || gallery.inert) return;
    const previous=selected;
    selected=index;
    const movingIndex=index>=0 ? index : previous;
    const source=regions[movingIndex];
    const to=index<0 ? resting : [];
    const towardRight=source.x+source.w/2<metrics.W/2;
    const towardBottom=source.y+source.h/2<metrics.H/2;
    if(index>=0) {
      const right=source.x+source.w;
      const bottom=source.y+source.h;
      const scale=Math.max(1,Math.min(2.6,metrics.W*.77/source.w,metrics.H*.74/source.h,
        (towardRight ? metrics.W-10-source.x : right-10)/source.w,
        (towardBottom ? metrics.H-58-source.y : bottom-54)/source.h));
      const w=source.w*scale, h=source.h*scale;
      const focus=box(towardRight ? source.x : right-w,towardBottom ? source.y : bottom-h,w,h);
      resting.forEach((region,i)=>{to[i]=i===index ? focus : pushAside(region,focus,metrics);});
    }
    close.hidden=index<0;
    gallery.classList.toggle('is-focused',index>=0);
    tiles.forEach(({button},i)=>{
      button.classList.toggle('is-selected',i===index || index<0 && i===previous);
      button.setAttribute('aria-pressed',String(i===index));
    });
    if(index>=0) {
      const item=items[index];
      if(articleTitle) articleTitle.href=item.url;
      caption.textContent=item.title;
    } else {
      tiles[previous].button.focus({preventScroll:true});
    }
    detail.hidden=true;
    if(reduced.matches) {
      regions=to;
      movement=undefined;
      gallery.removeAttribute('aria-busy');
      updateDetail();
    } else {
      movement={from:regions,to,index:movingIndex,towardRight,towardBottom,opening:index>=0};
      gallery.setAttribute('aria-busy','true');
    }
    requestRender();
  }
  close.addEventListener('click',()=>select(-1));
  gallery.addEventListener('click',event=>{
    if(selected>=0 && !event.target.closest('.gallery-tile,.gallery-close,.gallery-detail a')) select(-1);
  });
  gallery.addEventListener('keydown',event=>{
    if(event.key==='Escape' && selected>=0) {
      event.preventDefault();
      select(-1);
    }
  });

  function positions(m) {
    const {W,H,mobile}=m;
    const gutter=mobile ? 22 : Math.max(36,W*.08);
    const top=Math.max(42,Math.min(89,H*.12));
    const columns=Math.min(tiles.length,mobile ? (tiles.length>10 ? 3 : 2) : (article || tiles.length>10 ? 4 : 3));
    const rows=Math.ceil(tiles.length/columns);
    const deskWidth=Math.min(W-gutter*2,1160);
    const deskLeft=(W-deskWidth)/2;
    const deskTop=top+54;
    const deskHeight=Math.max(120,H-deskTop-66);
    const cellW=deskWidth/columns;
    const cellH=deskHeight/rows;
    heading.style.left=deskLeft+'px';
    heading.style.top=top+'px';
    close.style.right=deskLeft+'px';
    close.style.top=(top-10)+'px';
    return tiles.map(({item},i)=>{
      const ratio=article ? item.ratio || 16/9 : item.width/item.height;
      const row=Math.floor(i/columns);
      const rowCount=Math.min(columns,tiles.length-row*columns);
      const rowLeft=deskLeft+(columns-rowCount)*cellW*((row%2) ? .18 : .43);
      const size=.93+variation(i,0)*.24;
      const tileWidth=Math.min(cellW*size,cellH*(size+.10)*ratio);
      const tileHeight=tileWidth/ratio;
      const tilt=0;
      const x=rowLeft+(i%columns+.5)*cellW-tileWidth/2+(variation(i,2)-.5)*cellW*.30;
      const y=deskTop+(row+.5)*cellH-tileHeight/2+(variation(i,3)-.5)*cellH*.39;
      const left=Math.min(Math.max(x,8),W-8-tileWidth);
      const top=Math.min(Math.max(y,deskTop-10),H-24-tileHeight);
      return box(left,top,tileWidth,tileHeight,tilt);
    });
  }

  function layout(m) {
    movement=undefined;
    gallery.removeAttribute('aria-busy');
    resting=positions(m);
    regions=resting;
    if(selected>=0) {
      const index=selected;
      selected=-1;
      select(index);
    }
  }

  function updateDetail() {
    detail.hidden=selected<0;
    if (detail.hidden) return;
    const region=regions[selected];
    const bounds=box(region.x,region.y+region.h+8,region.w,42);
    place(detail,bounds);
  }

  function animateSelection() {
    const {from,to,index,towardRight,towardBottom,opening,throwing}=movement;
    const now=performance.now();
    movement.start ??= now;
    const t=clamp((now-movement.start)/(throwing ? 390 : 640));
    const growth=throwing ? 1-(1-t)**3 : ease(t,0,1);
    const card=mixBox(from[index],to[index],growth);
    regions=from.map((region,i)=>{
      if(i===index) return card;
      const destination=(opening || throwing) && region.w===to[i].w && region.h===to[i].h
        ? pushAside(region,card,metrics) : mixBox(region,to[i],growth);
      return mixBox(destination,to[i],ease(t,.70,1));
    });
    if(opening && t<.98) {
      cursor(agent,framePoint(card,towardRight ? card.w : 0,towardBottom ? card.h : 0),1,0,true);
    }
    if(t<1) {
      requestRender();
    } else {
      regions=to;
      movement=undefined;
      gallery.removeAttribute('aria-busy');
      if(selected<0) tiles[index].button.classList.remove('is-selected');
      updateDetail();
      const depart=afterClose;
      afterClose=undefined;
      depart?.();
    }
  }

  function closeBefore(depart) {
    if(!movement && selected<0) return false;
    if(selected>=0) select(-1);
    if(reduced.matches) return false;
    afterClose=depart;
    return true;
  }

  function render(amount,ready) {
    visible(gallery,amount>0 ? 1 : 0,ready);
    gallery.classList.toggle('gallery-ready',ready);
    if(amount<=0) {
      if(selected>=0 || movement) {
        selected=-1;
        afterClose=undefined;
        close.hidden=detail.hidden=true;
        gallery.classList.remove('is-focused');
        tiles.forEach(({button})=>{
          button.classList.remove('is-selected');
          button.setAttribute('aria-pressed','false');
        });
        layout(metrics);
      }
      return;
    }
    if(movement) animateSelection();
    else if(ready) updateDetail();

    headingText.render(ease(amount,0,.25));
    const opened=reduced.matches ? 1 : ease(amount,0,.24);
    tiles.forEach(({button},i)=>{
      const region=regions[i];
      button.style.opacity=String(opened);
      const w=region.w*(.94+.06*opened), h=region.h*(.94+.06*opened);
      place(button,box(region.x+(region.w-w)/2,region.y+(region.h-h)/2,w,h));
    });
    if(!ready) detail.hidden=true;
  }
  return {layout,render,closeBefore};
}

const photoGallery=createGallery('photos',photos);
const articleGallery=createGallery('articles',articles,true);
const afterTitle=panel=>panel.querySelector('[data-after-title]');
const reveals={intro:afterTitle(intro),about:afterTitle(about),contact:afterTitle(contact),projects:projectNodes.map(afterTitle)};
const getScramble = (node) => new Scramble(node.querySelector('[data-scramble]'));
const names = {
  intro:getScramble(intro),about:getScramble(about),
  contact:getScramble(contact),
  projects:projectNodes.map(getScramble),
};

function backspace(container) {
  const selector='[data-scramble], p, .tags li, a, .down, figcaption';
  const elements=container.matches(selector) ? [container] : [...container.querySelectorAll(selector)];
  const characters=[];
  const tags=[];
  for(const element of elements) {
    const glyphs=element.querySelectorAll('.scramble-glyph');
    if(glyphs.length) {
      characters.push(...glyphs);
      continue;
    }
    const original=element.textContent;
    const accessible=el('span',{class:'visually-hidden'},original);
    const display=el('span',{'aria-hidden':'true'});
    const first=characters.length;
    for(const char of Array.from(original)) {
      if (/\s/u.test(char)) display.append(char);
      else {
        const glyph=el('span',{class:'backspace-glyph'},char);
        display.append(glyph);
        characters.push(glyph);
      }
    }
    element.replaceChildren(accessible,display);
    if(element.matches('.tags li')) tags.push({element,first});
  }
  let previous=characters.length;
  let caret;
  return (amount,showCaret=true)=>{
    const remaining=characters.length-Math.ceil(clamp(amount)*characters.length);
    if(previous!==remaining) {
      const start=Math.min(previous,remaining), end=Math.max(previous,remaining);
      for(let i=start;i<end;i++) characters[i].classList.toggle('backspace-hidden',i>=remaining);
      for(const {element,first} of tags) element.classList.toggle('backspace-empty',remaining<=first);
      previous=remaining;
    }
    const next=showCaret && amount>0 && remaining>0 ? characters[remaining-1] : null;
    if(caret!==next) {
      caret?.classList.remove('backspace-caret');
      next?.classList.add('backspace-caret');
      caret=next;
    }
  };
}
const erase={
  intro:backspace(intro),about:backspace(about),
  projects:projectNodes.map(backspace),
};

function descriptionTyping(panel) {
  const description=panel.querySelector('[data-after-title] p, p[data-after-title]');
  const glyphs=Array.from(description.querySelectorAll('.backspace-glyph'));
  description.classList.add('flicker-copy');
  let previousFrame;
  return (progress,closing)=>{
    const frame=Math.floor(progress*16);
    const colorize=!closing && !reduced.matches && progress>0 && progress<1;
    const key=frame*2+Number(colorize);
    if(key===previousFrame) return;
    previousFrame=key;
    const edge=Math.ceil(glyphs.length/4)*progress;
    glyphs.forEach((glyph,index)=>{
      const group=Math.floor(index/4);
      const flashing=group>=edge-2 && group<edge+2;
      const printed=progress===1 || group<edge-1 || flashing && hash(group*223+frame*101)>.31;
      glyph.classList.toggle('description-hidden',!printed);
      if(colorize && printed && flashing) {
        glyph.dataset.ink=String((group+frame)%5);
      } else if(glyph.hasAttribute('data-ink')) {
        glyph.removeAttribute('data-ink');
      }
    });
  };
}
const describe={
  intro:descriptionTyping(intro),about:descriptionTyping(about),projects:projectNodes.map(descriptionTyping),
};
const millisecondsPerTimelineUnit=1500;
const introPause=1.15, aboutPause=1.25, projectPause=1.15, contactPause=1.80;
const timing = {
  introEnd:2.04+introPause,aboutLength:2.13+aboutPause,projectLength:2.22+projectPause,
  articleLength:5.32,photoLength:4.44,
};
// A hold consumes scroll distance while its visual progress remains fixed.
const holdAt=(progress,at,length)=>progress-Math.min(length,Math.max(0,progress-at));
timing.projectStart=timing.introEnd+timing.aboutLength;
timing.articleStart=timing.projectStart+projects.length*timing.projectLength;
timing.photoStart=timing.articleStart+timing.articleLength;
timing.contactStart=timing.photoStart+timing.photoLength;
timing.end=timing.contactStart+1.74+contactPause;
const sceneStops = [
  [0,0],
  [2.03,2.03+introPause],
  [timing.introEnd+1.96,timing.introEnd+1.96+aboutPause],
  ...projects.map((_,i)=>{
    const start=timing.projectStart+i*timing.projectLength+2.09;
    return [start,start+projectPause];
  }),
  [timing.articleStart+3.08,timing.articleStart+3.54],
  [timing.photoStart+2.19,timing.photoStart+2.71],
  [timing.contactStart+1.73,timing.end],
];
const jumps = {
  start:0,about:timing.introEnd+1.96,projects:sceneStops[3][0],photography:timing.photoStart+2.19,
  tecirc:timing.articleStart+3.08,contact:timing.contactStart+1.73,
};
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
let metrics, raf=0;
let sceneAnimation = 0, swipe, wheelTime = -Infinity, wheelDistance = 0, wheelUsed = false;
function cancelSceneAnimation() {
  cancelAnimationFrame(sceneAnimation);
  sceneAnimation=0;
}
document.querySelector('.skip').addEventListener('click',event=>{
  event.preventDefault();
  cancelSceneAnimation();
  go(sceneStops[1][0]);
  stage.focus({preventScroll:true});
});
const updateMotionPreference=()=>{cancelSceneAnimation();requestRender();};
if (reduced.addEventListener) reduced.addEventListener('change',updateMotionPreference);
else reduced.addListener(updateMotionPreference);

document.querySelectorAll('[data-jump]').forEach(a=>a.addEventListener('click',event=>{
  event.preventDefault();
  const target = a.dataset.jump;
  cancelSceneAnimation();
  go(jumps[target]);
  history.replaceState(null,'',target==='start' ? location.pathname+location.search : '#'+target);
}));
function go(y) {
  if (!metrics) return;
  window.scrollTo(0,y*metrics.unit);
  requestRender();
}
function progress() {
  return Math.max(0,Math.min(timing.end,window.scrollY/metrics.unit));
}
function stepScene(direction) {
  if (sceneAnimation || !metrics) return;
  const depart=()=>stepScene(direction);
  if(articleGallery.closeBefore(depart) || photoGallery.closeBefore(depart)) return;
  const position=progress(), tolerance=2/metrics.unit;
  const current=sceneStops.find(([start,end])=>position>=start-tolerance && position<=end+tolerance);
  const next=direction>0
    ? sceneStops.find(([start])=>start>(current?.[1] ?? position)+tolerance)
    : sceneStops.filter(([,end])=>end<(current?.[0] ?? position)-tolerance).pop();
  if (!next) return;
  const from=current ? current[direction>0 ? 1 : 0] : position;
  const to=next[direction>0 ? 0 : 1];
  const distance=Math.abs(to-from);
  let began;
  if(reduced.matches) { go(to); return; }
  const advance=now=>{
    began ??= now;
    const travelled=(now-began)/millisecondsPerTimelineUnit;
    const complete=travelled>=distance;
    // Each motion in render has its own easing; the shared timeline runs at a fixed rate.
    go(complete ? to : from+direction*travelled);
    sceneAnimation=complete ? 0 : requestAnimationFrame(advance);
  };
  sceneAnimation=requestAnimationFrame(advance);
}
window.addEventListener('wheel',event=>{
  if (event.ctrlKey || event.metaKey || Math.abs(event.deltaX)>Math.abs(event.deltaY)) return;
  event.preventDefault();
  const now=performance.now();
  if (now-wheelTime>180) {
    wheelDistance=0;
    wheelUsed=false;
  }
  wheelTime=now;
  if (wheelUsed) return;
  wheelDistance+=event.deltaY*(event.deltaMode===0 ? 1 : event.deltaMode===1 ? 16 : 100);
  if (Math.abs(wheelDistance)>=12) {
    wheelUsed=true;
    stepScene(Math.sign(wheelDistance));
  }
},{passive:false});
stage.addEventListener('touchstart',event=>{
  swipe=event.touches.length===1 && !event.target.closest('.gallery-titlebar') ? event.touches[0] : null;
},{passive:true});
stage.addEventListener('touchmove',event=>{
  if (!swipe || event.touches.length!==1) return;
  const touch=event.touches[0];
  if (Math.abs(touch.clientY-swipe.clientY)>Math.abs(touch.clientX-swipe.clientX) && event.cancelable) {
    event.preventDefault();
  }
},{passive:false});
stage.addEventListener('touchend',event=>{
  if (!swipe || event.touches.length) return;
  const end=Array.from(event.changedTouches).find(touch=>touch.identifier===swipe.identifier);
  const dx=end ? end.clientX-swipe.clientX : 0;
  const dy=end ? swipe.clientY-end.clientY : 0;
  swipe=null;
  if (Math.abs(dy)>=30 && Math.abs(dy)>Math.abs(dx)) stepScene(Math.sign(dy));
},{passive:true});
stage.addEventListener('touchcancel',()=>{swipe=null;},{passive:true});
window.addEventListener('keydown',event=>{
  if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.target.closest?.('input,textarea,select,[contenteditable]')) return;
  if (event.key===' ' && event.target.closest?.('button,a')) return;
  const direction=['ArrowDown','PageDown'].includes(event.key) || (event.key===' ' && !event.shiftKey) ? 1
    : ['ArrowUp','PageUp'].includes(event.key) || (event.key===' ' && event.shiftKey) ? -1 : 0;
  if (!direction) return;
  event.preventDefault();
  if (!event.repeat) stepScene(direction);
});
function resize() {
  const W = stage.clientWidth, H = stage.clientHeight;
  if(metrics?.W===W && metrics.H===H) return;
  const was=metrics ? progress() : 0;
  const mobile = W <= 650;
  const mid = W/2;
  const pad = mobile ? 23 : Math.max(52,W*.075);
  const frameWidth=Math.min(W-2*pad,880);
  const heights={
    dormant:Math.min(H*.55,425),
    about:Math.max(1,Math.min(H-120,mobile?340:434)),
    project:Math.max(1,Math.min(H-136,mobile?360:440)),
    contact:Math.max(1,Math.min(H-128,345)),
  };
  const frameTop=(H-Math.max(...Object.values(heights)))/2;
  const sizing={W,H,mobile,pad,unit:Math.max(mobile?440:620,Math.round(H*(mobile?1.20:1.23)))};
  for(const [name,height] of Object.entries(heights)) {
    sizing[name]=box(mid-frameWidth/2,frameTop,frameWidth,height);
  }
  metrics = sizing;
  photoGallery.layout(sizing);
  articleGallery.layout(sizing);
  experience.style.height = `${Math.floor(timing.end * sizing.unit) + H}px`;
  // Preserve the same frame through device rotation and viewport size changes.
  if (Math.abs(window.scrollY-was*sizing.unit) > 1) window.scrollTo(0,was*sizing.unit);
  render(progress(),metrics);
}
function requestRender() {
  if (raf) return;
  raf = requestAnimationFrame(()=>{
    raf = 0;
    if (metrics) render(progress(),metrics);
  });
}
window.addEventListener('scroll',requestRender,{passive:true});
window.addEventListener('resize',resize,{passive:true});

function showPanel(node,opacity,region) {
  if (region && opacity > .001) place(node,region);
  visible(node,opacity,opacity > .94);
}
let typingCursor;
function panelTyping(t,start,end,from,node,scramble) {
  scramble?.render(phase(t,start,end));
  const opacity=1-ease(t,start+.09,start+.15);
  if(t>=start-.18 && opacity>.001) {
    typingCursor={
      from,node,opacity,
      travel:ease(t,start-.18,start-.035),
      form:phase(t,start-.08,start+.065),
    };
  }
}
function paintTypingCursor() {
  stage.classList.toggle('cursor-handoff',Boolean(typingCursor));
  if(!typingCursor) return;
  const {from,node,opacity,travel,form}=typingCursor;
  stage.style.setProperty('--inline-caret-opacity',String(1-opacity));
  const active=node.querySelector('.scramble-caret,.backspace-caret');
  const glyph=active ?? node.querySelector('.scramble-slot,.backspace-glyph');
  const rect=glyph?.getBoundingClientRect();
  const stageRect=stage.getBoundingClientRect();
  const to=rect?.width ? point(
    (active?.classList.contains('backspace-caret') ? rect.right : rect.left)-stageRect.left,
    rect.top+rect.height/2-stageRect.top,
  ) : from;
  cursor(agent,mixPoint(from,to,travel),opacity,form,false,rect?.height);
}

function lowerCorner(region) {
  return point(region.x+region.w-1,region.y+region.h-1);
}
function approachFrame(region,travel,opacity) {
  const corner=lowerCorner(region);
  cursor(agent,mixPoint(point(corner.x+17,corner.y+14),corner,travel),opacity);
}
function retractFrame(region,progress) {
  const depth=1-ease(progress,0,.72);
  const top=1-ease(progress,.72,1);
  const origin=corner(region);
  const end=point(region.x+region.w-1,region.y);
  const tip=progress < .72 ? mixPoint(end,lowerCorner(region),depth) : mixPoint(origin,end,top);
  cursor(agent,tip,1-ease(progress,.96,1));
  return {depth,top,opacity:top > 0 ? 1 : 0};
}

function render(s,m) {
  let frameBox = m.dormant, frameAlpha = 0, frameTop = 1, frameDepth = 1;
  let aboutAlpha = 0, introAlpha = 0, projectAlpha = 0, projectIndex = -1;
  let photoBuild=0,articleBuild=0,contactAlpha=0;
  let introDetails=0,aboutDetails=0,projectDetails=0,contactDetails=0;
  let introErase=0,aboutErase=0,projectErase=0;
  typingCursor=null;
  visible(agent,0);
  visible(scrollHint,1-ease(s,.025,.20));

  if (s < timing.introEnd) {
    const t=holdAt(s,2.03,introPause);
    frameTop = ease(t,.15,.57);
    frameDepth = ease(t,.57,.82);
    frameAlpha = t > .145 ? 1 : 0;
    const origin = corner(m.dormant);
    if (t < .15) {
      cursor(agent,mixPoint(point(origin.x+30,origin.y-23),origin,ease(t,.01,.15)),ease(t,.01,.11));
    } else if(t < .82) {
      const tip = t < .57 ? mixPoint(origin,right(m.dormant),frameTop) : mixPoint(right(m.dormant),bottomRight(m.dormant),frameDepth);
      cursor(agent,tip,1);
    } else {
      panelTyping(t,1.13,1.61,bottomRight(m.dormant),names.intro.node,names.intro);
    }
    introAlpha = ease(t,.98,1.15);
    introDetails=phase(t,1.61,2.03);
  } else if (s < timing.projectStart) {
    const t=holdAt(s-timing.introEnd,1.96,aboutPause);
    const bend=ease(t,.38,.66);
    frameBox = mixBox(m.dormant,m.about,bend);
    frameAlpha = 1;
    introErase=phase(t,.06,.34);
    introAlpha=introErase<1 ? 1 : 0;
    aboutAlpha=ease(t,.66,.82);
    names.intro.render(1);
    introDetails=1;
    aboutDetails=phase(t,1.42,1.95);
    if(t < .68) {
      if(t>=.34) approachFrame(frameBox,ease(t,.34,.50),ease(t,.34,.43));
    } else {
      panelTyping(t,.86,1.42,lowerCorner(frameBox),names.about.node,names.about);
    }
    names.about.render(phase(t,.86,1.42));
  } else if (s < timing.articleStart) {
    const elapsed = s-timing.projectStart;
    projectIndex = Math.min(projects.length-1,Math.floor(elapsed/timing.projectLength));
    const t=holdAt(elapsed-projectIndex*timing.projectLength,2.09,projectPause);
    if (t < .45) {
      const from = projectIndex===0 ? m.about : m.project;
      frameBox=from;
      frameAlpha=1;
      aboutErase=phase(t,0,.18);
      aboutAlpha=projectIndex===0 && aboutErase<1 ? 1 : 0;
      names.about.render(1);
      aboutDetails=1;
      if(t<.20) approachFrame(from,ease(t,.10,.20),ease(t,.10,.17));
      else ({top:frameTop,depth:frameDepth,opacity:frameAlpha}=retractFrame(from,phase(t,.20,.45)));
    } else {
      frameBox=m.project;
      frameTop=ease(t,.48,.72);
      frameDepth=ease(t,.72,.91);
      frameAlpha = t>=.48 ? 1 : 0;
      projectAlpha=t>=.91 ? 1 : 0;
      if(t < .91) {
        const tip = t < .48 ? mixPoint(corner(projectIndex===0 ? m.about : m.project),corner(frameBox),ease(t,.45,.48)) : t < .72 ?
          mixPoint(corner(frameBox),right(frameBox),frameTop) : mixPoint(right(frameBox),bottomRight(frameBox),frameDepth);
        cursor(agent,tip,1);
      } else {
        const title=names.projects[projectIndex];
        panelTyping(t,1.12,1.60,bottomRight(frameBox),title.node,title);
      }
    }
    if(projectIndex>0 && t < .18) {
      projectAlpha=1;
      projectErase=phase(t,0,.18);
      projectIndex--;
      projectDetails=1;
    }
    const closingPrevious=projectIndex<Math.floor(elapsed/timing.projectLength);
    names.projects[projectIndex].render(closingPrevious ? 1 : phase(t,1.12,1.60));
    if (!closingPrevious) projectDetails=phase(t,1.60,2.08);
  } else if(s < timing.photoStart) {
    const elapsed=s-timing.articleStart;
    frameBox=m.project;
    if (elapsed<.32) {
      frameAlpha=1;
      if(elapsed<.15) approachFrame(frameBox,ease(elapsed,.06,.15),ease(elapsed,.06,.12));
      else ({top:frameTop,depth:frameDepth,opacity:frameAlpha}=retractFrame(frameBox,phase(elapsed,.15,.32)));
    }
    projectErase=phase(elapsed,0,.15);
    projectAlpha=projectErase<1 ? 1 : 0;
    projectIndex=projects.length-1;
    names.projects[projectIndex]?.render(1);
    projectDetails=1;
    articleBuild=phase(elapsed,.32,2.56)*(1-phase(elapsed,3.59,timing.articleLength));
  } else if(s < timing.contactStart) {
    const elapsed=s-timing.photoStart;
    photoBuild=phase(elapsed,0,1.70)*(1-phase(elapsed,2.75,timing.photoLength));
  } else {
    const t=holdAt(s-timing.contactStart,1.73,contactPause);
    frameBox=m.contact;
    frameTop=ease(t,.20,.51);
    frameDepth=ease(t,.51,.72);
    frameAlpha=ease(t,.16,.23);
    contactAlpha=ease(t,.73,.90);
    contactDetails=ease(t,1.62,1.72);
    if(t < .72) {
      const tip = t < .20 ? mixPoint(point(m.pad,m.H*.53),corner(frameBox),ease(t,.02,.20)) :
        t < .51 ? mixPoint(corner(frameBox),right(frameBox),frameTop) : mixPoint(right(frameBox),bottomRight(frameBox),frameDepth);
      cursor(agent,tip,ease(t,.02,.13));
    } else {
      panelTyping(t,.93,1.62,bottomRight(frameBox),names.contact.node,names.contact);
    }
  }

  drawFrame(frame,frameBox,frameTop,frameDepth,frameAlpha);
  showPanel(intro,introAlpha,frameBox);
  showPanel(about,aboutAlpha,frameBox);
  showPanel(projectPanel,projectAlpha,frameBox);
  projectNodes.forEach((node,i)=>{
    node.hidden=i!==projectIndex;
    node.querySelector('.project-visual').style.clipPath='inset(0 '+projectErase*100+'% 0 0)';
  });
  showPanel(contact,contactAlpha,m.contact);
  erase.intro(introErase);
  erase.about(aboutErase);
  describe.intro(introDetails,introErase>0);
  describe.about(aboutDetails,aboutErase>0);
  visible(reveals.intro,introDetails>0 ? 1 : 0);
  visible(reveals.about,aboutDetails>0 ? 1 : 0);
  visible(reveals.about.querySelector('.tags'),aboutDetails===1 ? 1 : 0);
  visible(reveals.contact,contactDetails,contactAlpha>.94 && contactDetails>.95);
  reveals.projects.forEach((node,i)=>{
    const opacity=i===projectIndex ? projectDetails : 0;
    const amount=i===projectIndex ? projectErase : 0;
    erase.projects[i](amount);
    describe.projects[i](opacity,amount>0);
    visible(node,opacity>0 ? 1 : 0);
    visible(node.querySelector('a'),opacity===1 ? 1 : 0,opacity===1 && projectAlpha>.94 && amount===0);
  });
  photoGallery.render(photoBuild,photoBuild>=1);
  articleGallery.render(articleBuild,articleBuild>=1);
  paintTypingCursor();
}

const initial = location.hash.substring(1);
if ('scrollRestoration' in history) history.scrollRestoration='manual';
document.documentElement.classList.add('immersive');
experience.hidden=false;
resize();
go(Object.hasOwn(jumps,initial) ? jumps[initial] : 0);
