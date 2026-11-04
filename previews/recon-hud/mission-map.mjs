import {terrain} from './world-view.mjs';
import {labelFor,communicationPulse,communicationColors} from './renderer.mjs';
export function mapSnapshot(mission,frames,selected=0,playing=true){
 return {kind:'map-frame',version:1,cycle:mission.cycle,elapsed:mission.elapsed,stage:mission.stage,selected,playing,
  nodes:frames.map((frame,index)=>({id:index,position:[...frame.pose.position],heading:frame.pose.heading,state:mission.nodes[index].state,status:frame.presentationStatus,active:frame.presentationStatus==='airborne',phase:mission.nodes[index].phase,communication:mission.communications[index]??null})),
  // Camera sprites have no global contact coordinates. These fixed report
  // locations are illustrative placements, never inferred world truth.
  reports:mission.nodes.flatMap((scene,index)=>{
   if(scene.designation?.kind==='friendly'&&scene.designation.source===index)return [{source:index,kind:'blue',position:[100,180],label:'BLUE REPORT'}];
   if(['TARGET','ENGAGE','ZOOM'].includes(scene.state))return [{source:index,kind:'red',position:[145,145],label:'RED REPORT'}];
   return [];
  })};
}
export function validMapSnapshot(s){
 return s?.kind==='map-frame'&&s.version===1&&Number.isInteger(s.cycle)&&s.cycle>=0&&Number.isFinite(s.elapsed)&&Number.isInteger(s.selected)&&s.selected>=0&&s.selected<16&&typeof s.stage==='string'&&s.stage.length<32&&Array.isArray(s.nodes)&&s.nodes.length===16&&s.nodes.every((n,i)=>n.id===i&&['airborne','parked','lost'].includes(n.status)&&n.active===(n.status==='airborne')&&Array.isArray(n.position)&&n.position.length===3&&n.position.every(v=>Number.isFinite(v)&&Math.abs(v)<100000)&&Number.isFinite(n.heading)&&typeof n.state==='string'&&n.state.length<32&&Number.isFinite(n.phase)&&(!n.communication||['TX','RX'].includes(n.communication.direction)&&Number.isFinite(n.communication.age)))&&Array.isArray(s.reports)&&s.reports.length<=16&&s.reports.every(r=>Number.isInteger(r.source)&&r.source>=0&&r.source<16&&['red','blue'].includes(r.kind)&&Array.isArray(r.position)&&r.position.length===2&&r.position.every(v=>Number.isFinite(v)&&Math.abs(v)<100000));
}
export function flashFor(node){const c=node.communication;return c&&communicationPulse(c.age)?communicationColors[c.direction]:null;}
export function drawMap(canvas,s){
 const ratio=globalThis.devicePixelRatio||1,w=canvas.clientWidth||640,h=canvas.clientHeight||360;
 const width=Math.round(w*ratio),height=Math.round(h*ratio);
 if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}
 const ctx=canvas.getContext('2d');ctx.save();ctx.scale(ratio,ratio);
 const scale=Math.min((w-70)/320,(h-60)/310),left=(w-320*scale)/2,top=(h-310*scale)/2;
 const point=([x,y])=>[left+(x+80)*scale,top+(210-y)*scale];
 ctx.fillStyle='#06110d';ctx.fillRect(0,0,w,h);
 ctx.save();ctx.beginPath();ctx.rect(left,top,320*scale,310*scale);ctx.clip();
 ctx.fillStyle='#253728';ctx.fillRect(left,top,320*scale,310*scale);
 // The same 24-unit fields and seed used beneath the camera views. This is
 // flat presentation terrain, not an elevation or navigability model.
 for(let x=-96;x<240;x+=24)for(let y=-120;y<210;y+=24){
  const shade=terrain(x+12,y+12,271828);if(shade===1)continue;
  ctx.fillStyle=shade===2?'#3d5033':'#57563a';
  const [px,py]=point([x+3,y+20]);ctx.fillRect(px,py,17*scale,17*scale);
 }
 ctx.strokeStyle='#97ae7930';ctx.lineWidth=.5;
 for(let x=-72;x<=240;x+=24){ctx.beginPath();ctx.moveTo(...point([x,-100]));ctx.lineTo(...point([x,210]));ctx.stroke();}
 for(let y=-96;y<=210;y+=24){ctx.beginPath();ctx.moveTo(...point([-80,y]));ctx.lineTo(...point([240,y]));ctx.stroke();}
 ctx.restore();
 ctx.font='12px monospace';ctx.fillStyle='#a3b6aa';ctx.fillText('N ↑',20,25);ctx.fillText('FICTIONAL WORLD',20,h-18);
 for(const report of s.reports){
  const [x,y]=point(report.position);ctx.fillStyle=report.kind==='blue'?'#4695ff':'#ff5757';
  for(const [dx,dy] of [[-4,0],[4,0],[0,5]])ctx.fillRect(x+dx-1,y+dy-1,3,3);
 }
 // Report key carries provenance once per type, avoiding stacked map labels.
 const reports=[...new Set(s.reports.map(r=>r.kind))];
 reports.forEach((kind,i)=>{ctx.fillStyle=kind==='blue'?'#4695ff':'#ff5757';ctx.fillText(kind.toUpperCase()+' REPORT · ILLUSTRATIVE',20,48+i*18);});
 const labels=[],large=w>=900;
 const labelWidth=large?21:16,labelHeight=large?15:12;
 for(const n of s.nodes){
  const [x,y]=point(n.position),lost=n.status==='lost',flash=flashFor(n);
  ctx.fillStyle=lost?'#ed6868':n.id===s.selected?'#ffffff':n.active?'#80dcf2':'#81948a';ctx.strokeStyle=ctx.fillStyle;
  ctx.beginPath();ctx.arc(x,y,n.id===s.selected?6:large?4:3,0,Math.PI*2);ctx.fill();
  if(lost){ctx.beginPath();ctx.moveTo(x-6,y-6);ctx.lineTo(x+6,y+6);ctx.moveTo(x-6,y+6);ctx.lineTo(x+6,y-6);ctx.stroke();}
  if(n.active){const angle=n.heading*Math.PI/180;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+Math.sin(angle)*14,y-Math.cos(angle)*14);ctx.stroke();}
  if(flash){ctx.strokeStyle=flash;ctx.lineWidth=2;const radius=large?9:6;ctx.strokeRect(x-radius,y-radius,radius*2,radius*2);ctx.lineWidth=1;ctx.fillStyle=flash;}
  ctx.font=(large?'14':'11')+'px monospace';
  let label=null;
  for(const [dx,dy] of [[8,-8],[8,14],[-22,-8],[-22,14],[0,-20],[0,24]]){
   const q={x:Math.max(2,Math.min(w-18,x+dx)),y:Math.max(12,Math.min(h-20,y+dy))};
   if(labels.every(b=>Math.abs(b.x-q.x)>labelWidth+2||Math.abs(b.y-q.y)>labelHeight+1)){label=q;break;}
  }
  if(label){labels.push(label);const color=ctx.fillStyle;ctx.fillStyle='#06110d';ctx.fillRect(label.x-1,label.y-labelHeight+2,labelWidth,labelHeight);ctx.fillStyle=color;ctx.fillText(labelFor(n.id),label.x,label.y);}

 }
 ctx.restore();
 canvas.dataset.positions=JSON.stringify(s.nodes.map(n=>n.position));
 canvas.dataset.flashes=JSON.stringify(s.nodes.map(flashFor));
 canvas.dataset.elapsed=String(s.elapsed);
 canvas.dataset.statuses=JSON.stringify(s.nodes.map(n=>n.status));
 canvas.setAttribute('aria-label',`Mission ${s.cycle+1}, ${s.stage}. ${s.nodes.filter(n=>n.active).length} airborne nodes, ${s.nodes.filter(n=>n.status==='lost').length} lost nodes held at their last position. ${s.nodes.filter(flashFor).map(n=>labelFor(n.id)+' '+n.communication.direction).join(', ')}. Scripted reports: ${reports.join(', ')||'none'}.`);
}
export function installFullscreen(section,button,status){
 const update=()=>{button.textContent=document.fullscreenElement===section||section.classList.contains('map-expanded')?'Exit full screen':'Full screen';};
 button.addEventListener('click',async()=>{
  try{
   if(document.fullscreenElement===section)await document.exitFullscreen();
   else if(section.classList.contains('map-expanded'))section.classList.remove('map-expanded');
   else if(document.fullscreenEnabled&&section.requestFullscreen)await section.requestFullscreen();
   else section.classList.add('map-expanded');
  }catch{section.classList.toggle('map-expanded');if(status)status.textContent='Expanded in this window.';}
  update();
 });
 document.addEventListener('fullscreenchange',update);
 document.addEventListener('keydown',e=>{if(e.key==='Escape'){section.classList.remove('map-expanded');update();}});
}

export function observeMapSize(canvas,getSnapshot){const observer=new ResizeObserver(()=>{const s=getSnapshot();if(s)drawMap(canvas,s);});observer.observe(canvas);return observer;}
