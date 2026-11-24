import { profile, photos, articles, projects } from './content.js';
import { box, bottomRight, clamp, cursor, ease, mixBox, mixPoint, phase, place, point, hash, Scramble, visible } from './motion.js';

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
  const img = el('img',{src:source,alt,decoding:'async',class:pictureClass,draggable:'false'});
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
  const gap=-Math.min(region.w,region.h)*.30;
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
    const overlap = overlapX*overlapY/(region.w*region.h);
    return Math.max(0,overlap-.18)*320+Math.hypot(x-region.x,y-region.y);
  };
  const [x,y]=options.reduce((best,candidate)=>score(candidate)<score(best) ? candidate : best);
  return box(x,y,region.w,region.h,region.rotation);
}

// A single mask reveals horizontal bands of the existing window in both directions.
function windowFlicker(progress,index,tick,closing) {
  const edge=band=>{
    const seed=index*337+band*23+tick*59;
    const blend=ease(progress*18-tick,0,1);
    const jitter=hash(seed)*(1-blend)+hash(seed+59)*blend-.5;
    return 100*clamp(progress+jitter*.46*Math.sin(Math.PI*progress));
  };
  const bands=Array.from({length:6},(_,band)=>{
    const x=(closing ? 100-edge(band) : edge(band)).toFixed(2)+'%';
    return x+' '+(band*100/6)+'%, '+x+' '+((band+1)*100/6)+'%';
  });
  const fixed=closing ? 100 : 0;
  return 'polygon('+fixed+'% 0, '+bands.join(', ')+', '+fixed+'% 100%)';
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
  if(articleTitle) {
    articleTitle.classList.add('visually-labeled-link');
    articleTitle.draggable=false;
  }
  detail.append(articleTitle ?? photoName);
  if(article) detail.classList.add('article-image-link');
  const tiles=items.map((item,index)=>{
    const visual=artwork(item,'gallery-image');
    const titlebar=el('span',{class:'gallery-titlebar','aria-hidden':'true'},item.title);
    const button=el('button',{
      class:'gallery-tile',type:'button','aria-label':item.title,'aria-pressed':'false',title:item.title,
    },titlebar,visual);
    button.addEventListener('click',event=>{
      if(event.detail && ignoreClick===index) { ignoreClick=-1; return; }
      if(article && selected===index) return;
      select(selected===index ? -1 : index);
    });
    button.addEventListener('pointerdown',event=>beginDrag(event,index));
    gallery.append(button);
    const glyphs=Array.from(item.title, char=>el('span',{},char));
    titlebar.replaceChildren(...glyphs);
    return {item,button,glyphs};
  });
  gallery.append(close,detail);
  articleTitle?.addEventListener('pointerdown',event=>beginDrag(event,selected));
  articleTitle?.addEventListener('click',event=>{
    if(ignoreClick===selected) {
      event.preventDefault();
      ignoreClick=-1;
    }
  });

  let selected=-1, regions, resting, movement, afterClose, drag, ignoreClick=-1;
  function beginDrag(event,index) {
    if(!event.isPrimary || event.button!==0 || index<0 || gallery.inert || (movement && !movement.throwing)) return;
    if(movement) {
      movement=undefined;
      if(selected<0) resting=regions;
      gallery.removeAttribute('aria-busy');
    }
    ignoreClick=-1;
    drag={index,id:event.pointerId,x:event.clientX,y:event.clientY,from:regions,lastX:event.clientX,lastY:event.clientY,lastTime:event.timeStamp,vx:0,vy:0};
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  gallery.addEventListener('pointermove',event=>{
    if(drag?.id!==event.pointerId) return;
    const dx=event.clientX-drag.x, dy=event.clientY-drag.y;
    if(!drag.moved && Math.hypot(dx,dy)<6) return;
    drag.moved=true;
    tiles[drag.index].button.classList.add('is-dragging');
    const dt=event.timeStamp-drag.lastTime;
    if(dt>0) {
      drag.vx=drag.vx*.44+(event.clientX-drag.lastX)/dt*.56;
      drag.vy=drag.vy*.44+(event.clientY-drag.lastY)/dt*.56;
      drag.lastX=event.clientX;
      drag.lastY=event.clientY;
      drag.lastTime=event.timeStamp;
    }
    const origin=drag.from[drag.index];
    const x=Math.max(5,Math.min(metrics.W-origin.w-5,origin.x+dx));
    const y=Math.max(5,Math.min(metrics.H-origin.h-5,origin.y+dy));
    const card=box(x,y,origin.w,origin.h);
    const originRegions=drag.destinations ?? regions;
    drag.destinations=originRegions.map((region,i)=>i===drag.index ? card : pushAside(region,card,metrics));
    regions=regions.map((region,i)=>i===drag.index ? card : region);
    requestRender();
  });
  function endDrag(event) {
    if(drag?.id!==event.pointerId) return;
    const {index,moved,vx,vy,lastTime,destinations}=drag;
    drag=undefined;
    tiles[index].button.classList.remove('is-dragging');
    if(!moved) return;
    ignoreClick=index;
    const from=regions;
    const landed=from[index];
    const coast=event.type==='pointerup' && event.timeStamp-lastTime<115 ? 200 : 0;
    const offset=value=>Math.max(-280,Math.min(280,value*coast));
    const target=box(Math.max(5,Math.min(metrics.W-landed.w-5,landed.x+offset(vx))),
      Math.max(5,Math.min(metrics.H-landed.h-5,landed.y+offset(vy))),landed.w,landed.h);
    if(reduced.matches) {
      if(selected<0) resting=regions;
      return;
    }
    const to=(destinations ?? from).map((region,i)=>i===index ? target : pushAside(region,target,metrics));
    if(selected<0) resting=to;
    movement={from,to,index,throwing:true};
    gallery.setAttribute('aria-busy','true');
    requestRender();
  }
  gallery.addEventListener('pointerup',endDrag);
  gallery.addEventListener('pointercancel',endDrag);
  gallery.addEventListener('lostpointercapture',endDrag);
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
      (articleTitle ?? photoName).textContent=item.title;
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
    drag=undefined;
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
    const bounds=article ? box(region.x,region.y+20,region.w,region.h-20)
      : box(region.x,region.y+region.h+8,region.w,42);
    place(detail,bounds);
  }

  function animateSelection() {
    const {from,to,index,towardRight,towardBottom,opening,throwing}=movement;
    const now=performance.now();
    movement.start ??= now;
    const t=clamp((now-movement.start)/(throwing ? 860 : 980));
    const growth=throwing ? (1-Math.exp(-4.5*t))/(1-Math.exp(-4.5)) : ease(t,0,.84);
    const card=mixBox(from[index],to[index],growth);
    regions=from.map((region,i)=>{
      if(i===index) return card;
      const travel=opening ? ease(t,.14,1) : throwing ? ease(t,.10,1) : ease(t,.04,1);
      return mixBox(region,to[i],travel);
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

  function render(amount,ready,closing) {
    visible(gallery,amount>0 ? 1 : 0,ready);
    gallery.classList.toggle('gallery-ready',ready);
    if(amount<=0) {
      if(selected>=0 || movement || drag) {
        selected=-1;
        afterClose=undefined;
        close.hidden=detail.hidden=true;
        gallery.classList.remove('is-focused');
        tiles.forEach(({button})=>{
          button.classList.remove('is-selected','is-dragging');
          button.setAttribute('aria-pressed','false');
        });
        layout(metrics);
      }
      return;
    }
    if(movement) {
      animateSelection();
      if(ready && movement?.throwing) updateDetail();
    } else if(drag?.destinations) {
      let settling=false;
      regions=regions.map((region,i)=>{
        const target=drag.destinations[i];
        if(Math.hypot(target.x-region.x,target.y-region.y)<.5 || reduced.matches) return target;
        settling=true;
        return mixBox(region,target,.24);
      });
      if(settling) requestRender();
      if(ready) updateDetail();
    } else if(ready) updateDetail();

    headingText.render(ease(amount,0,.25));
    const opened=reduced.matches ? 1 : closing ? ease(amount,0,1) : 1-(1-amount)**1.65;
    tiles.forEach(({button,glyphs},i)=>{
      const region=regions[i];
      const reveal=reduced.matches ? 1 : opened**(1+(i%4)*.055);
      const active=reveal>0 && reveal<1;
      const tick=Math.floor(reveal*18);
      button.style.opacity=String(reveal===0 ? 0 : 1);
      button.style.clipPath=active ? windowFlicker(reveal,i,tick,closing) : '';
      if(button.dataset.flicker!==String(active ? tick : -1)) {
        button.dataset.flicker=String(active ? tick : -1);
        glyphs.forEach((glyph,j)=>{
          const ink=active && glyph.textContent.trim() && hash(j*31+i*23+tick*7)>.72;
          if(ink) glyph.dataset.ink=String((i+j+tick)%5);
          else delete glyph.dataset.ink;
        });
      }
      const w=region.w*(.94+.06*opened), h=region.h*(.94+.06*opened);
      const drift=closing && !reduced.matches ? (1-reveal)*24 : 0;
      place(button,box(region.x+(region.w-w)/2+drift,region.y+(region.h-h)/2+drift*.42,w,h));
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
    const tick=Math.floor(amount*18);
    const isFlickering=!reduced.matches && amount>0 && amount<1;
    characters.forEach((glyph,i)=>{
      const nearEdge=i<remaining && i>=remaining-7;
      const flicker=isFlickering && nearEdge && glyph.textContent.trim();
      glyph.classList.toggle('erase-flicker-off',Boolean(flicker && hash(i*13+tick*71)<.18));
      if(flicker && hash(i*37+tick*19)>.35)
        glyph.dataset.eraseInk=String((i+tick)%5);
      else if(glyph.hasAttribute('data-erase-ink')) delete glyph.dataset.eraseInk;
    });
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

function descriptionTyping(description) {
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
const describePanel=panel=>descriptionTyping(panel.querySelector('[data-after-title] p, p[data-after-title]'));
const describe={
  intro:describePanel(intro),about:describePanel(about),projects:projectNodes.map(describePanel),
};
const aboutTags=reveals.about.querySelector('.tags');
const revealTags=descriptionTyping(aboutTags);
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
  [timing.articleStart+1.40,timing.articleStart+3.54],
  [timing.photoStart+1.12,timing.photoStart+2.71],
  [timing.contactStart+1.73,timing.end],
];
const jumps = {
  start:0,about:timing.introEnd+1.96,projects:sceneStops[3][0],photography:timing.photoStart+1.12,
  tecirc:timing.articleStart+1.40,contact:timing.contactStart+1.73,
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
  swipe=event.touches.length===1 && !event.target.closest('.gallery-ready .gallery-tile,.gallery-ready .article-image-link') ? event.touches[0] : null;
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
function render(s,m) {
  let frameBox = m.dormant;
  let aboutAlpha = 0, introAlpha = 0, projectAlpha = 0, projectIndex = -1;
  let photoBuild=0,articleBuild=0,contactAlpha=0,photoClosing=false,articleClosing=false;
  let introDetails=0,aboutDetails=0,projectDetails=0,contactDetails=0;
  let introErase=0,aboutErase=0,projectErase=0;
  typingCursor=null;
  visible(agent,0);
  visible(scrollHint,1-ease(s,.025,.20));

  if (s < timing.introEnd) {
    const t=holdAt(s,2.03,introPause);
    panelTyping(t,1.13,1.61,bottomRight(m.dormant),names.intro.node,names.intro);
    introAlpha = ease(t,.98,1.15);
    introDetails=phase(t,1.61,2.03);
  } else if (s < timing.projectStart) {
    const t=holdAt(s-timing.introEnd,1.96,aboutPause);
    const bend=ease(t,.38,.66);
    frameBox = mixBox(m.dormant,m.about,bend);
    introErase=phase(t,.06,.34);
    introAlpha=introErase<1 ? 1 : 0;
    aboutAlpha=ease(t,.66,.82);
    names.intro.render(1);
    introDetails=1;
    aboutDetails=phase(t,1.42,1.95);
    panelTyping(t,.86,1.42,lowerCorner(frameBox),names.about.node,names.about);
    names.about.render(phase(t,.86,1.42));
  } else if (s < timing.articleStart) {
    const elapsed = s-timing.projectStart;
    projectIndex = Math.min(projects.length-1,Math.floor(elapsed/timing.projectLength));
    const t=holdAt(elapsed-projectIndex*timing.projectLength,2.09,projectPause);
    if (t < .45) {
      const from = projectIndex===0 ? m.about : m.project;
      frameBox=from;
      aboutErase=phase(t,0,.18);
      aboutAlpha=projectIndex===0 && aboutErase<1 ? 1 : 0;
      names.about.render(1);
      aboutDetails=1;
    } else {
      frameBox=m.project;
      projectAlpha=t>=.91 ? 1 : 0;
      const title=names.projects[projectIndex];
      panelTyping(t,1.12,1.60,bottomRight(frameBox),title.node,title);
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
    projectErase=phase(elapsed,0,.15);
    projectAlpha=projectErase<1 ? 1 : 0;
    projectIndex=projects.length-1;
    names.projects[projectIndex]?.render(1);
    projectDetails=1;
    articleClosing=elapsed>3.59;
    articleBuild=phase(elapsed,.18,1.38)*(1-phase(elapsed,3.59,4.58));
  } else if(s < timing.contactStart) {
    const elapsed=s-timing.photoStart;
    photoClosing=elapsed>2.75;
    photoBuild=phase(elapsed,0,1.10)*(1-phase(elapsed,2.75,3.74));
  } else {
    const t=holdAt(s-timing.contactStart,1.73,contactPause);
    frameBox=m.contact;
    contactAlpha=ease(t,.73,.90);
    contactDetails=ease(t,1.62,1.72);
    panelTyping(t,.93,1.62,bottomRight(frameBox),names.contact.node,names.contact);
  }

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
  describe.about(phase(aboutDetails,0,.69),aboutErase>0);
  const tagProgress=phase(aboutDetails,.69,1);
  revealTags(tagProgress,aboutErase>0);
  visible(reveals.intro,introDetails>0 ? 1 : 0);
  visible(reveals.about,aboutDetails>0 ? 1 : 0);
  visible(aboutTags,tagProgress>0 ? 1 : 0);
  visible(reveals.contact,contactDetails,contactAlpha>.94 && contactDetails>.95);
  reveals.projects.forEach((node,i)=>{
    const opacity=i===projectIndex ? projectDetails : 0;
    const amount=i===projectIndex ? projectErase : 0;
    erase.projects[i](amount);
    describe.projects[i](opacity,amount>0);
    visible(node,opacity>0 ? 1 : 0);
    visible(node.querySelector('a'),opacity===1 ? 1 : 0,opacity===1 && projectAlpha>.94 && amount===0);
  });
  photoGallery.render(photoBuild,photoBuild>=1,photoClosing);
  articleGallery.render(articleBuild,articleBuild>=1,articleClosing);
  paintTypingCursor();
}

const initial = location.hash.substring(1);
if ('scrollRestoration' in history) history.scrollRestoration='manual';
document.documentElement.classList.add('immersive');
experience.hidden=false;
resize();
go(Object.hasOwn(jumps,initial) ? jumps[initial] : 0);

