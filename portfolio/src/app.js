import { profile, photos, articles, projects } from './content.js';
import { box, clamp, ease, mixBox, phase, place, hash, visible } from './motion.js';

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
aboutContent(about.querySelector('.about-content'));
profileLinks(contact.querySelector('.profile-links'));

const projectNodes = projects.map(item=>{
  const node = el('div',{class:'project-item',hidden:''},projectContent(item));
  projectPanel.append(node);
  return node;
});
function galleryMargin(layout) {
  return layout.dormant.x+layout.panelInset;
}

function createGallery(id,items,article=false) {
  const gallery=byId(id);
  const heading=gallery.querySelector('h2');
  const eraseHeading=backspace(heading);
  const revealHeading=descriptionTyping(heading,1);
  const seed=Math.floor(Math.random()*32768);
  const variation=(index,channel)=>hash(seed+index*397+channel*883);
  const backdrop=el('div',{class:'gallery-backdrop','aria-hidden':'true'});
  const detail=article ? el('div',{class:'gallery-detail article-image-link',hidden:''}) : null;
  const articleTitle=article ? articleLink(items[0]) : null;
  if(articleTitle) {
    articleTitle.classList.add('visually-labeled-link');
    articleTitle.draggable=false;
  }

  const tiles=items.map((item,index)=>{
    const visual=artwork(item,'gallery-image');
    const titlebar=el('span',{class:'gallery-titlebar','aria-hidden':'true'},item.title);
    const button=el('button',{
      class:'gallery-tile',type:'button','aria-label':item.title,'aria-pressed':'false',title:item.title,
    },titlebar,visual);
    button.addEventListener('click',()=>{
      if(selected<0 && !movement) select(index);
    });
    gallery.append(button);
    return {item,button};
  });
  gallery.append(backdrop);
  if(detail) {
    detail.append(articleTitle);
    gallery.append(detail);
  }

  let selected=-1, regions, resting, movement, afterClose;
  function previewBox(index) {
    const {W,H,mobile}=metrics;
    const item=items[index];
    const ratio=article ? item.ratio || 16/9 : item.width/item.height;
    const margin=article ? galleryMargin(metrics) : mobile ? 12 : 30;
    const verticalReserve=article && mobile ? 94 : 46;
    const width=Math.min(W-2*margin,Math.max(1,H-verticalReserve)*ratio);
    const height=width/ratio+20;
    return box((W-width)/2,(H-height)/2+(article && mobile ? 12 : 0),width,height);
  }
  function syncSelection(active) {
    gallery.classList.toggle('is-focused',active);
    tiles.forEach(({button},i)=>{
      button.inert=active && i!==selected;
      button.setAttribute('aria-pressed',String(i===selected));
    });
  }
  function select(index) {
    if(index===selected || gallery.inert) return;
    const previous=selected;
    const movingIndex=index>=0 ? index : previous;
    selected=index;
    syncSelection(index>=0);
    tiles[movingIndex].button.classList.add('is-selected');
    if(index>=0) {
      const item=items[index];
      if(articleTitle) {
        articleTitle.href=item.url;
        articleTitle.replaceChildren(item.title);
      }
      tiles[index].button.focus({preventScroll:true});
    } else {
      tiles[previous].button.focus({preventScroll:true});
    }
    if(detail) detail.hidden=true;
    movement={from:regions[movingIndex],to:index>=0 ? previewBox(index) : resting[movingIndex],
      index:movingIndex,opening:index>=0,backdropFrom:Number(backdrop.style.opacity)};
    gallery.setAttribute('aria-busy','true');
    requestRender();
  }
  backdrop.addEventListener('click',()=>select(-1));
  gallery.addEventListener('keydown',event=>{
    if(event.key==='Escape' && selected>=0) {
      event.preventDefault();
      select(-1);
    }
  });

  function positions(m) {
    const {W,H,mobile}=m;
    const wideArticles=article && W>=900;
    const deskLeft=galleryMargin(m);
    const top=Math.max(42,Math.min(89,H*.12));
    const desktopColumns=article && (W<900 || H<620) || tiles.length>10 ? 4 : 3;
    const columns=Math.min(tiles.length,mobile ? (tiles.length>10 ? 3 : 2) : desktopColumns);
    const rows=Math.ceil(tiles.length/columns);
    const deskWidth=W-2*deskLeft;
    const deskTop=top+(wideArticles ? 44 : article ? 54 : 38);
    const deskHeight=Math.max(120,H-deskTop-(article && !wideArticles ? 66 : 24));
    const cellW=deskWidth/columns;
    const cellH=deskHeight/rows;
    heading.style.left=deskLeft+'px';
    heading.style.top=top+'px';
    return tiles.map(({item},i)=>{
      const ratio=article ? item.ratio || 16/9 : item.width/item.height;
      const row=Math.floor(i/columns);
      const rowCount=Math.min(columns,tiles.length-row*columns);
      const rowLeft=deskLeft+(columns-rowCount)*cellW*((row%2) ? .18 : .43);
      const size=wideArticles ? .90+variation(i,0)*.07 : article ? .67+variation(i,0)*.23 : .89+variation(i,0)*.06;
      const tileWidth=Math.min(cellW*size,cellH*size*ratio);
      const tileHeight=tileWidth/ratio;
      const tilt=0;
      const x=rowLeft+(i%columns+.5)*cellW-tileWidth/2+(variation(i,2)-.5)*cellW*(article && !wideArticles ? .20 : .045);
      const y=deskTop+(row+.5)*cellH-tileHeight/2+(variation(i,3)-.5)*cellH*(article && !wideArticles ? .20 : .045);
      const left=Math.min(Math.max(x,deskLeft),W-deskLeft-tileWidth);
      const top=Math.min(Math.max(y,deskTop-10),H-24-tileHeight);
      return box(left,top,tileWidth,tileHeight,tilt);
    });
  }

  function layout(m) {
    resting=positions(m);
    regions=[...resting];
    movement=undefined;
    gallery.removeAttribute('aria-busy');
    if(selected>=0) {
      regions[selected]=previewBox(selected);
      backdrop.style.opacity='1';
      updateDetail();
    } else {
      tiles.forEach(({button})=>button.classList.remove('is-selected'));
      backdrop.style.opacity='0';
    }
  }

  function updateDetail() {
    if(!detail) return;
    detail.hidden=selected<0;
    if (detail.hidden) return;
    const region=regions[selected];
    const bounds=box(region.x,region.y+20,region.w,region.h-20);
    place(detail,bounds);
  }

  function animateSelection() {
    const now=performance.now();
    movement.start ??= now;
    const {from,to,index,opening,backdropFrom}=movement;
    const t=reduced.matches ? 1 : clamp((now-movement.start)/(opening ? 440 : 320));
    const progress=opening ? 1-(1-t)**3 : ease(t,0,1);
    regions[index]=mixBox(from,to,progress);
    backdrop.style.opacity=String(backdropFrom+((opening ? 1 : 0)-backdropFrom)*progress);
    if(t<1) {
      requestRender();
      return;
    }
    movement=undefined;
    gallery.removeAttribute('aria-busy');
    if(!opening) tiles[index].button.classList.remove('is-selected');
    updateDetail();
    const depart=afterClose;
    afterClose=undefined;
    depart?.();
  }

  function closeBefore(depart) {
    if(!movement && selected<0) return false;
    if(selected>=0) select(-1);
    afterClose=depart;
    return true;
  }

  function render(amount,ready,closing) {
    visible(gallery,amount>0 ? 1 : 0,ready);
    gallery.classList.toggle('gallery-ready',ready);
    if(amount<=0) {
      if(selected>=0 || movement) {
        selected=-1;
        afterClose=undefined;
        if(detail) detail.hidden=true;
        syncSelection(false);
        layout(metrics);
      }
      return;
    }
    if(movement) animateSelection();

    const headingProgress=reduced.matches ? 1 : ease(amount,0,.68);
    revealHeading(closing ? 1 : headingProgress,false);
    eraseHeading(closing ? 1-headingProgress : 0);
    heading.style.visibility=headingProgress>0 ? 'visible' : 'hidden';
    const opened=reduced.matches ? 1 : closing ? ease(amount,0,1) : 1-(1-amount)**1.65;
    tiles.forEach(({button},i)=>{
      button.style.opacity=String(opened);
      place(button,regions[i]);
    });
    if(!ready && detail) detail.hidden=true;
  }
  return {layout,render,closeBefore};
}

const photoGallery=createGallery('photos',photos);
const articleGallery=createGallery('articles',articles,true);
const afterTitle=panel=>panel.querySelector('[data-after-title]');
const reveals={intro:afterTitle(intro),about:afterTitle(about),contact:afterTitle(contact),projects:projectNodes.map(afterTitle)};
function backspace(container) {
  const selector='[data-scramble], [data-flicker], h2, p, .tags li, a, .down, figcaption';
  const elements=container.matches(selector) ? [container] : [...container.querySelectorAll(selector)];
  const characters=[];
  const tags=[];
  for(const element of elements) {
    const original=element.textContent;
    const accessible=el('span',{class:'visually-hidden'},original);
    const display=el('span',{'aria-hidden':'true'});
    for(const char of Array.from(original)) {
      if (/\s/u.test(char)) display.append(char);
      else {
        const glyph=el('span',{class:'backspace-glyph'},char);
        display.append(glyph);
        characters.push(glyph);
      }
    }
    element.replaceChildren(accessible,display);
    if(element.matches('.tags li')) tags.push({element,end:characters.length});
  }
  let previous=0;
  return amount=>{
    const erased=Math.floor(clamp(amount)*characters.length);
    if(previous!==erased) {
      const start=Math.min(previous,erased), end=Math.max(previous,erased);
      for(let i=start;i<end;i++) characters[i].classList.toggle('backspace-hidden',i<erased);
      for(const {element,end} of tags) element.classList.toggle('backspace-empty',end<=erased);
      previous=erased;
    }
    const tick=Math.floor(amount*18);
    const isFlickering=!reduced.matches && amount>0 && amount<1;
    characters.forEach((glyph,i)=>{
      const nearEdge=i>=erased && i<erased+7;
      const flicker=isFlickering && nearEdge && glyph.textContent.trim();
      glyph.classList.toggle('erase-flicker-off',Boolean(flicker && hash(i*13+tick*71)<.18));
      if(flicker && hash(i*37+tick*19)>.35)
        glyph.dataset.eraseInk=String((i+tick)%5);
      else if(glyph.hasAttribute('data-erase-ink')) delete glyph.dataset.eraseInk;
    });

  };
}
const erase={
  intro:backspace(intro),about:backspace(about),
  projects:projectNodes.map(backspace),
};

function descriptionTyping(description,groupSize=4) {
  const glyphs=Array.from(description.querySelectorAll('.backspace-glyph'));
  description.classList.add('flicker-copy');
  let previousFrame;
  return (progress,closing)=>{
    const frame=Math.floor(progress*16);
    const colorize=!closing && !reduced.matches && progress>0 && progress<1;
    const key=frame*2+Number(colorize);
    if(key===previousFrame) return;
    previousFrame=key;
    const edge=Math.ceil(glyphs.length/groupSize)*progress;
    glyphs.forEach((glyph,index)=>{
      const group=Math.floor(index/groupSize);
      const flashing=group>=edge-2 && group<edge+2;
      const printed=progress===1 || progress>0 && (group<edge-1 || flashing && hash(group*223+frame*101)>.31);
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
backspace(contact);
const eraseScrollWord=backspace(scrollHint.querySelector('[data-flicker]'));
const titleTyping=panel=>descriptionTyping(panel.querySelector('[data-scramble]'),1);
const names={
  intro:titleTyping(intro),about:titleTyping(about),contact:titleTyping(contact),
  projects:projectNodes.map(titleTyping),
};
const projectLinks=reveals.projects.map(node=>descriptionTyping(node.querySelector('a'),1));
const revealSocials=descriptionTyping(reveals.contact,2);
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
  if (sceneAnimation || wavePointer!==null || !metrics) return;
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
  swipe=event.touches.length===1 ? event.touches[0] : null;
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
  const panelInset=parseFloat(getComputedStyle(intro).paddingLeft);
  const sizing={W,H,mobile,pad,panelInset,unit:Math.max(mobile?440:620,Math.round(H*(mobile?1.20:1.23)))};
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

const scrollWave=el('div',{
  class:'scroll-wave',tabindex:'0',role:'slider','aria-label':'スクロール位置',
  'aria-orientation':'vertical','aria-valuemin':'0','aria-valuemax':'100','aria-valuenow':'0',
});
const waveMarks=Array.from({length:25},()=>el('i',{'aria-hidden':'true'}));
scrollWave.append(...waveMarks);
document.body.append(scrollWave);
let waveFrame=0, wavePosition, waveWake, waveTarget=0, waveEnergy=0, waveTime=0;

let wavePointer=null;
let waveTrack;

function seekWave(fraction) {
  cancelSceneAnimation();
  go(clamp(fraction)*timing.end);
}

function seekWavePointer(event) {
  const {start,end}=waveTrack;
  seekWave((event.clientY-start)/Math.max(1,end-start));
}

scrollWave.addEventListener('pointerdown',event=>{
  if(!event.isPrimary || event.button!==0 || wavePointer!==null || !metrics) return;
  event.preventDefault();
  articleGallery.closeBefore();
  photoGallery.closeBefore();
  scrollWave.focus({preventScroll:true});
  const first=waveMarks[0].getBoundingClientRect();
  const last=waveMarks.at(-1).getBoundingClientRect();
  waveTrack={start:first.top+first.height/2,end:last.top+last.height/2};
  wavePointer=event.pointerId;
  scrollWave.setPointerCapture(wavePointer);
  scrollWave.classList.add('is-dragging');
  seekWavePointer(event);
});
scrollWave.addEventListener('pointermove',event=>{
  if(event.pointerId===wavePointer) seekWavePointer(event);
});
function endWaveDrag(event) {
  if(event.pointerId!==wavePointer) return;
  if(event.type==='pointerup') seekWavePointer(event);
  wavePointer=null;
  scrollWave.classList.remove('is-dragging');
}
for(const eventName of ['pointerup','pointercancel','lostpointercapture']) {
  scrollWave.addEventListener(eventName,endWaveDrag);
}

scrollWave.addEventListener('keydown',event=>{
  const current=progress()/timing.end;
  const targets={Home:0,End:1,ArrowUp:current-.025,ArrowDown:current+.025,
    ArrowLeft:current-.025,ArrowRight:current+.025,PageUp:current-.12,PageDown:current+.12};
  if(!Object.hasOwn(targets,event.key) || event.altKey || event.ctrlKey || event.metaKey) return;
  event.preventDefault();
  articleGallery.closeBefore();
  photoGallery.closeBefore();
  scrollWave.focus({preventScroll:true});
  seekWave(targets[event.key]);
});

function drawScrollWave(now) {
  waveFrame=0;
  const dt=Math.min(48,Math.max(1,now-waveTime));
  waveTime=now;
  wavePosition+=(waveTarget-wavePosition)*(1-Math.exp(-dt/75));
  if(wavePointer!==null) wavePosition=waveTarget;
  waveWake+=(wavePosition-waveWake)*(1-Math.exp(-dt/130));
  waveEnergy*=Math.exp(-dt/280);
  if(reduced.matches) {
    wavePosition=waveWake=waveTarget;
    waveEnergy=0;
  }
  waveMarks.forEach((mark,i)=>{
    const position=i/(waveMarks.length-1);
    const peak=Math.exp(-.5*((position-wavePosition)/.045)**2);
    const ripple=Math.exp(-.5*((position-waveWake)/(.075+waveEnergy*.16))**2)*waveEnergy;
    mark.style.opacity=String(.38+peak*.52+ripple*.28);
    mark.style.transform=`scaleX(${.65+peak*.35+ripple*.40})`;
    mark.style.backgroundPosition=`${waveWake*100+ripple*60}% 50%`;
  });
  if(waveEnergy>.003 || Math.abs(waveWake-waveTarget)>.0001 ||
      Math.abs(wavePosition-waveTarget)>.0001) waveFrame=requestAnimationFrame(drawScrollWave);
}

function updateScrollWave(s) {
  const next=clamp(s/timing.end);
  if(wavePosition===undefined) wavePosition=waveWake=next;
  if(Math.abs(next-waveTarget)>.00001) waveEnergy=Math.min(1,.38+Math.abs(next-waveTarget)*50);
  waveTarget=next;
  scrollWave.setAttribute('aria-valuenow',String(Math.round(next*100)));
  if(!waveFrame) waveFrame=requestAnimationFrame(drawScrollWave);
}

function showPanel(node,opacity,region) {
  if (region && opacity > .001) place(node,region);
  visible(node,opacity,opacity > .94);
}
// Keep the reveal deterministic when scrolling back through the same frame.
const logoColumns=8, logoRows=5;
// The reveal advances rightward, with neighboring columns allowed to interleave.
const logoRevealOrder=tile=>tile%logoColumns+1.6*hash(181+tile*173);
const logoTiles=Array.from({length:logoColumns*logoRows},(_,i)=>i)
  .sort((a,b)=>logoRevealOrder(a)-logoRevealOrder(b));
const logoPalette=['#26e7a0','#b58cff','#ffe44d','#ff86ce','#69cbff'];

// Give the tiles a small overlap so the clip does not show antialiasing seams.
const logoTileBleed=.0025;
const clipNamespace='http://www.w3.org/2000/svg';
const logoClips=projectNodes.map((_,i)=>{
  const svg=document.createElementNS(clipNamespace,'svg');
  svg.setAttribute('aria-hidden','true');
  svg.setAttribute('width','0');
  svg.setAttribute('height','0');
  svg.style.position='absolute';
  const defs=document.createElementNS(clipNamespace,'defs');
  const clip=document.createElementNS(clipNamespace,'clipPath');
  clip.id='logo-reveal-'+i;
  clip.setAttribute('clipPathUnits','objectBoundingBox');
  const rects=logoTiles.map(tile=>{
    const rect=document.createElementNS(clipNamespace,'rect');
    const x=(tile%logoColumns)/logoColumns;
    const y=Math.floor(tile/logoColumns)/logoRows;
    const left=Math.max(0,x-logoTileBleed), top=Math.max(0,y-logoTileBleed);
    rect.setAttribute('x',String(left));
    rect.setAttribute('y',String(top));
    rect.setAttribute('width',String(Math.min(1,x+1/logoColumns+logoTileBleed)-left));
    rect.setAttribute('height',String(Math.min(1,y+1/logoRows+logoTileBleed)-top));
    clip.append(rect);
    return rect;
  });
  defs.append(clip);
  svg.append(defs);
  document.body.append(svg);
  return {clip,rects};
});

function paintLogo(visual,progress,{clip,rects}) {
  if(progress>=1 || reduced.matches) {
    visual.style.clipPath='none';
    visual.style.removeProperty('--logo-flash');
    return;
  }
  const frame=Math.floor(progress*24);
  const flashes=[];
  logoTiles.forEach((tile,rank)=>{
    const distance=progress*logoTiles.length-rank;
    const settled=distance>5;
    const shown=settled || (progress>0 && distance>=-3 && hash(tile*191+frame*67)>=.36);
    rects[rank].style.display=shown ? '' : 'none';
    if(shown && !settled) {
      const color=logoPalette[(tile+frame)%logoPalette.length]+'b8';
      const x=100*(tile%logoColumns)/(logoColumns-1);
      const y=100*Math.floor(tile/logoColumns)/(logoRows-1);
      const bleed=logoTileBleed*100;
      flashes.push(`linear-gradient(${color}, ${color}) ${x}% ${y}% / ${100/logoColumns+bleed*2}% ${100/logoRows+bleed*2}% no-repeat`);
    }
  });
  visual.style.clipPath='url(#'+clip.id+')';
  if(flashes.length) visual.style.setProperty('--logo-flash',flashes.join(', '));
  else visual.style.removeProperty('--logo-flash');
}
function render(s,m) {
  updateScrollWave(s);
  let frameBox = m.dormant;
  let aboutAlpha = 0, introAlpha = 0, projectAlpha = 0, projectIndex = -1;
  let photoBuild=0,articleBuild=0,contactAlpha=0,photoClosing=false,articleClosing=false;
  let introDetails=0,aboutDetails=0,projectDetails=0,contactDetails=0;
  let introErase=0,aboutErase=0,projectErase=0,logoProgress=0;
  const hintProgress=phase(s,.025,.20);
  eraseScrollWord(hintProgress);
  scrollHint.querySelector('.scroll-arrow').style.opacity=String(1-hintProgress);
  visible(scrollHint,Number(hintProgress<1));

  if (s < timing.introEnd) {
    const t=holdAt(s,2.03,introPause);
    names.intro(phase(t,.23,1.61));
    introAlpha = ease(t,.18,.34);
    introDetails=phase(t,1.61,2.03);
  } else if (s < timing.projectStart) {
    const t=holdAt(s-timing.introEnd,1.96,aboutPause);
    introErase=phase(t,.06,.34);
    introAlpha=introErase<1 ? 1 : 0;
    aboutAlpha=ease(t,.34,.49);
    names.intro(1);
    introDetails=1;
    aboutDetails=phase(t,1.42,1.95);
    names.about(phase(t,.39,1.42));
  } else if (s < timing.articleStart) {
    const elapsed = s-timing.projectStart;
    projectIndex = Math.min(projects.length-1,Math.floor(elapsed/timing.projectLength));
    const t=holdAt(elapsed-projectIndex*timing.projectLength,2.09,projectPause);
    if (t < .20) {
      const from = projectIndex===0 ? m.about : m.project;
      frameBox=from;
      aboutErase=phase(t,0,.18);
      aboutAlpha=projectIndex===0 && aboutErase<1 ? 1 : 0;
      names.about(1);
      aboutDetails=1;
    } else {
      frameBox=m.project;
      projectAlpha=t>=.22 ? 1 : 0;
      logoProgress=phase(t,.22,1.55);
    }
    if(projectIndex>0 && t < .18) {
      projectAlpha=1;
      projectErase=phase(t,0,.18);
      logoProgress=1-projectErase;
      projectIndex--;
      projectDetails=1;
    }
    const closingPrevious=projectIndex<Math.floor(elapsed/timing.projectLength);
    names.projects[projectIndex](closingPrevious ? 1 : phase(t,.29,1.60));
    if (!closingPrevious) projectDetails=phase(t,1.60,2.08);
  } else if(s < timing.photoStart) {
    const elapsed=s-timing.articleStart;
    frameBox=m.project;
    projectErase=phase(elapsed,0,.15);
    logoProgress=1-projectErase;
    projectAlpha=projectErase<1 ? 1 : 0;
    projectIndex=projects.length-1;
    names.projects[projectIndex](1);
    projectDetails=1;
    articleClosing=elapsed>3.59;
    articleBuild=phase(elapsed,.06,1.38)*(1-phase(elapsed,3.59,5.25));
  } else if(s < timing.contactStart) {
    const elapsed=s-timing.photoStart;
    photoClosing=elapsed>2.75;
    photoBuild=phase(elapsed,0,1.10)*(1-phase(elapsed,2.75,4.38));
  } else {
    const t=holdAt(s-timing.contactStart,1.73,contactPause);
    frameBox=m.contact;
    contactAlpha=ease(t,.04,.19);
    contactDetails=phase(t,1.45,1.72);
    names.contact(phase(t,.12,1.45));
  }

  showPanel(intro,introAlpha,frameBox);
  showPanel(about,aboutAlpha,m.about);
  showPanel(projectPanel,projectAlpha,frameBox);
  projectNodes.forEach((node,i)=>{
    node.hidden=i!==projectIndex;
    if(i===projectIndex) paintLogo(node.querySelector('.project-visual'),logoProgress,logoClips[i]);
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
  revealSocials(contactDetails,false);
  visible(reveals.contact,Number(contactDetails>0),contactAlpha>.94 && contactDetails===1);
  reveals.projects.forEach((node,i)=>{
    const opacity=i===projectIndex ? projectDetails : 0;
    const amount=i===projectIndex ? projectErase : 0;
    erase.projects[i](amount);
    describe.projects[i](opacity,amount>0);
    visible(node,opacity>0 ? 1 : 0);
    projectLinks[i](phase(opacity,.65,1),amount>0);
    visible(node.querySelector('a'),opacity>.65 ? 1 : 0,opacity===1 && projectAlpha>.94 && amount===0);
  });
  photoGallery.render(photoBuild,photoBuild>=1,photoClosing);
  articleGallery.render(articleBuild,articleBuild>=1,articleClosing);
}

const initial = location.hash.substring(1);
if ('scrollRestoration' in history) history.scrollRestoration='manual';
document.documentElement.classList.add('immersive');
experience.hidden=false;
resize();
go(Object.hasOwn(jumps,initial) ? jumps[initial] : 0);
