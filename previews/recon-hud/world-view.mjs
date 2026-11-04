import {fonts,palettes,labelFor} from './renderer.mjs';
import {northArrow,normalizeHeading} from './compass.mjs';
// Pure presentation geometry. Invented world units; no flight dynamics.
// +X right/east, +Y forward/north, +Z up. Angles in degrees; heading clockwise
// from +Y, pitch positive up, roll rotates camera right toward camera up.
export const view={left:0,right:63,top:8,bottom:49,cx:31.5,cy:28.5,focal:42};
const finite=n=>typeof n==='number'&&Number.isFinite(n);
const integer=(n,max)=>Number.isInteger(n)&&n>=0&&n<=max;
const position=p=>Array.isArray(p)&&p.length===3&&Array.from(p).every(n=>finite(n)&&Math.abs(n)<=100000)&&p[2]>=0;
export function validateSnapshot(s){
 if(!s||s.version!==1)return 'Unsupported snapshot';
 if(!integer(s.node,15)||!integer(s.run,0xffffffff)||!integer(s.seq,0xffffffff)||!integer(s.seed,0xffffffff))return 'Invalid identity or sequence';
 if(!finite(s.timeMs)||s.timeMs<0)return 'Invalid timestamp';
 if(typeof s.label!=='string'||! /^[A-Z ]{1,8}$/.test(s.label))return 'Invalid label';
 if(!s.pose||!position(s.pose.position)||!['heading','pitch','roll'].every(k=>finite(s.pose[k])&&Math.abs(s.pose[k])<=36000)||Math.abs(s.pose.pitch)>90)return 'Invalid camera pose';
 for(const key of ['peers','observations']){
  if(!Array.isArray(s[key])||s[key].length>16)return 'Too many or missing sightings';
  const ids=new Set();
  for(const p of s[key]){
   if(!p||!integer(p.id,15)||ids.has(p.id)||!position(p.position)||!finite(p.observedMs)||p.observedMs<0||p.observedMs>s.timeMs)return 'Invalid sighting';
   ids.add(p.id);
  }
 }
 if(s.stage!==undefined&&!['air','impact','ground','static'].includes(s.stage))return 'Invalid presentation stage';
 if(s.effectAgeMs!==undefined&&(!finite(s.effectAgeMs)||s.effectAgeMs<0))return 'Invalid effect age';
 return null;
}
const radians=n=>n*Math.PI/180;
function basis(pose){
 const h=radians(pose.heading),p=radians(pose.pitch),r=radians(pose.roll),sh=Math.sin(h),ch=Math.cos(h),sp=Math.sin(p),cp=Math.cos(p),sr=Math.sin(r),cr=Math.cos(r);
 const forward=[sh*cp,ch*cp,sp],right=[ch,-sh,0],up=[-sh*sp,-ch*sp,cp];
 return {forward,right:right.map((n,i)=>n*cr+up[i]*sr),up:up.map((n,i)=>n*cr-right[i]*sr)};
}
const dot=(a,b)=>a.reduce((sum,n,i)=>sum+n*b[i],0);
export function projectPoint(pose,point){
 const b=basis(pose),delta=point.map((n,i)=>n-pose.position[i]),depth=dot(delta,b.forward),horizontal=dot(delta,b.right),vertical=dot(delta,b.up);
 return {x:view.cx+view.focal*horizontal/Math.max(depth,.001),y:view.cy-view.focal*vertical/Math.max(depth,.001),behind:depth<=.001,horizontal,vertical,depth};
}
function ray(b,x,y){return b.forward.map((n,i)=>n+b.right[i]*(x-view.cx)/view.focal+b.up[i]*(view.cy-y)/view.focal);}
export function groundAtPixel(pose,x,y){
 const direction=ray(basis(pose),x,y);if(direction[2]>=-.00001||pose.position[2]<=0)return null;
 const t=-pose.position[2]/direction[2];return [pose.position[0]+direction[0]*t,pose.position[1]+direction[1]*t,0];
}
function hash(x,y,seed){let n=(Math.imul(x,73856093)^Math.imul(y,19349663)^seed)>>>0;n=Math.imul(n^(n>>>16),0x45d9f3b);return (n^(n>>>16))>>>0;}
const colors={cam:[[94,121,137],[65,76,49],[93,100,62],[126,118,76],[173,198,205]],night:[[6,17,13],[16,43,32],[36,65,52],[58,89,69],[146,245,173]],whitehot:[[28,28,28],[64,64,64],[89,89,89],[113,113,113],[155,155,155]]};
export function terrain(x,y,seed){const cell=hash(Math.floor(x/24),Math.floor(y/24),seed),gx=((x%24)+24)%24,gy=((y%24)+24)%24;return cell%4>0&&gx>3&&gx<20&&gy>3&&gy<20?2+cell%2:1;}
export function renderWorldCamera(snapshot,{sensor='night',output=new Uint8ClampedArray(64*64*4)}={}){
 const error=validateSnapshot(snapshot);if(error)throw new TypeError(error);
 if(!(output instanceof Uint8ClampedArray)||output.length!==16384)throw new TypeError('Invalid frame buffer');
 const table=colors[sensor]??colors[sensor==='blackhot'?'whitehot':'night'],b=basis(snapshot.pose);
 for(let i=0;i<output.length;i+=4){output[i]=6;output[i+1]=17;output[i+2]=13;output[i+3]=255;}
 for(let y=8;y<50;y++)for(let x=0;x<64;x++){
  const offset=(y*64+x)*4;
  if(snapshot.stage==='static'){
   const v=24+hash(x,y,snapshot.seed+Math.floor((snapshot.effectAgeMs??0)/125))%88;
   for(let c=0;c<3;c++)output[offset+c]=v;continue;
  }
  const direction=ray(b,x,y);let shade=0;
  if(direction[2]<0){const t=-snapshot.pose.position[2]/direction[2];shade=t<1800?terrain(snapshot.pose.position[0]+direction[0]*t,snapshot.pose.position[1]+direction[1]*t,snapshot.seed):1;}
  if(Math.abs(direction[2])<.008)shade=4;
  for(let c=0;c<3;c++)output[offset+c]=sensor==='blackhot'?255-table[shade][c]:table[shade][c];
  const mix=snapshot.stage==='ground'?1:snapshot.stage==='impact'?Math.max(0,Math.min(1,((snapshot.effectAgeMs??0)-1500)/500)):0;
  if(mix){
   const grain=hash(Math.floor(x/3)+Math.floor(snapshot.pose.position[0]*8),Math.floor(y/3)+Math.floor(snapshot.pose.position[1]*8),snapshot.seed)%4;
   const soil=sensor==='cam'?[[51,39,27],[73,55,37],[96,71,46],[121,91,59]][grain]:table[1+grain%3];
   for(let c=0;c<3;c++){const value=sensor==='blackhot'?255-soil[c]:soil[c];output[offset+c]=Math.round(output[offset+c]*(1-mix)+value*mix);}
  }
 }
 return output;
}

const clampTo=(n,min,max)=>Math.max(min,Math.min(max,n));
// Stable identity order and a bounded label budget keep this tiny view legible.
export function layoutSightings(snapshot){
 const error=validateSnapshot(snapshot);if(error)throw new TypeError(error);
 if(snapshot.stage&&snapshot.stage!=='air')return {markers:[],omitted:0};
 const fresh=snapshot.peers.filter(p=>p.id!==snapshot.node&&snapshot.timeMs-p.observedMs<1500).sort((a,b)=>a.id-b.id),markers=[];
 for(const peer of fresh){
  if(markers.length===3)break;
  const p=projectPoint(snapshot.pose,peer.position),inside=!p.behind&&p.x>=1&&p.x<=62&&p.y>=9&&p.y<=48;
  let x=p.x,y=p.y,kind=inside?'visible':p.behind?'rear':'edge';
  if(!inside){
   let dx=p.horizontal,dy=-p.vertical;
   // Exactly rearward has no lateral bearing: use a labelled bottom cue.
   if(Math.abs(dx)+Math.abs(dy)<.00001){dx=0;dy=1;}
   const scale=1/Math.max(Math.abs(dx)/30.5,Math.abs(dy)/19.5);
   x=view.cx+dx*scale;y=view.cy+dy*scale;
  }
  x=Math.round(clampTo(x,1,62));y=Math.round(clampTo(y,9,48));
  const text=(kind==='rear'?'R':'')+labelFor(peer.id),width=text.length*4-1;
  let box=null;
  for(const [ox,oy] of [[3,-6],[-width-3,-6],[3,3],[-width-3,3],[3,-13],[-width-3,10]]){
   const candidate={x:clampTo(x+ox,1,63-width),y:clampTo(y+oy,9,44),width};
   if(fresh.length>3&&candidate.x<14&&candidate.y+5>43)continue;
   if(markers.every(m=>candidate.x>m.box.x+m.box.width+1||m.box.x>candidate.x+width+1||candidate.y>m.box.y+6||m.box.y>candidate.y+6)){box=candidate;break;}
  }
  if(box)markers.push({id:peer.id,x,y,kind,text,box});
 }
 return {markers,omitted:fresh.length-markers.length};
}
function drawSightings(snapshot,pen,sensor){
 if(snapshot.stage&&snapshot.stage!=='air')return;
 for(const observation of snapshot.observations){
  if(snapshot.timeMs-observation.observedMs>=1500)continue;
  const p=projectPoint(snapshot.pose,observation.position);
  if(!p.behind&&p.x>=1&&p.x<=62&&p.y>=9&&p.y<=48)pen.pixel(p.x,p.y,sensor==='whitehot'?'#000000':'#ffffff');
 }
 const {markers,omitted}=layoutSightings(snapshot);
 for(const m of markers){
  const color='#80dcf2';
  if(m.kind==='visible'){
   pen.pixel(m.x,m.y,color);pen.pixel(m.x-1,m.y,color);pen.pixel(m.x+1,m.y,color);
  }else{
   const dx=view.cx-m.x,dy=view.cy-m.y,length=Math.hypot(dx,dy);
   for(let t=0;t<7;t+=2)pen.pixel(m.x+dx/length*t,m.y+dy/length*t,color);
  }
 }
 for(const m of markers){
  // Dark backing makes neutral IDs readable in every camera palette.
  for(let y=m.box.y;y<m.box.y+5;y++)for(let x=m.box.x;x<m.box.x+m.box.width;x++)pen.pixel(x,y,'#06110d');
  pen.text(m.box.x,m.box.y,m.text,'#80dcf2');
 }
 if(omitted){const text='+'+omitted;for(let y=44;y<49;y++)for(let x=1;x<1+text.length*4;x++)pen.pixel(x,y,'#06110d');pen.text(1,44,text,'#80dcf2');}
}
function painter(output){
 const cache=new Map();
 function pixel(x,y,color){x=Math.round(x);y=Math.round(y);if(x<0||x>63||y<0||y>63)return;let rgb=cache.get(color);if(!rgb){rgb=color.slice(1).match(/../g).map(n=>parseInt(n,16));cache.set(color,rgb);}const i=(y*64+x)*4;for(let c=0;c<3;c++)output[i+c]=rgb[c];output[i+3]=255;}
 function line(ax,ay,bx,by,color){const steps=Math.ceil(Math.max(Math.abs(bx-ax),Math.abs(by-ay)));for(let i=0;i<=steps;i++){const t=steps?i/steps:0;pixel(ax+(bx-ax)*t,ay+(by-ay)*t,color);}}
 function text(x,y,value,color){for(const c of value){(fonts[c]??fonts['?']).forEach((row,j)=>[...row].forEach((v,i)=>{if(v==='1')pixel(x+i,y+j,color);}));x+=4;}}
 return {pixel,line,text};
}
export function renderWorldView(snapshot,{sensor='night',palette='phosphor',status='LIVE',output,metrics=null}={}){
 const frame=renderWorldCamera(snapshot,{sensor,output}),p=palettes[palette]??palettes.phosphor,pen=painter(frame);
 drawSightings(snapshot,pen,sensor);
 if(snapshot.stage==='static'){
  for(let y=25;y<36;y++)for(let x=8;x<56;x++)pen.pixel(x,y,'#000000');
  pen.text(10,28,'SIGNAL LOST','#e1e8e9');
 }
 const heading=Math.round(normalizeHeading(snapshot.pose.heading))%360;
 pen.text(2,1,labelFor(snapshot.node),p.ink);
 const arrow=northArrow(heading),point=([x,y])=>[14+x,3+y];
 for(const end of ['tail','left','right'])pen.line(...point(arrow[end]),...point(arrow.tip),p.ink);
 pen.text(21,1,({cam:'TV',night:'NV',whitehot:'WH',blackhot:'BH',ir:'IR'})[sensor]??'NV',p.dim);
 pen.text(33,1,String(heading).padStart(3,'0'),p.dim);pen.text(50,1,metrics?.distance!=null?String(Math.min(999,Math.round(metrics.distance))).padStart(3,'0'):'D--',p.accent);pen.line(1,7,62,7,p.dim);
 pen.line(1,50,62,50,p.dim);pen.text(2,52,status==='LIVE'?snapshot.label:status,p.ink);pen.text(metrics?44:38,52,metrics?['OK','LOW','RTN'][metrics.reserve]:'NR-:--',p.dim);
 pen.text(2,58,'ALT '+Math.round(snapshot.pose.position[2]),p.dim);pen.text(metrics?46:48,58,metrics?'E'+String(Math.round(metrics.energy/100)).padStart(3,'0'):'BAT?',p.dim);
 return frame;
}

export function renderWorldWaiting(node,{palette='phosphor',output=new Uint8ClampedArray(16384)}={}){
 if(!integer(node,15)||!(output instanceof Uint8ClampedArray)||output.length!==16384)throw new TypeError('Invalid waiting frame');
 output.fill(0);for(let i=3;i<output.length;i+=4)output[i]=255;
 const p=palettes[palette]??palettes.phosphor,pen=painter(output);
 pen.text(2,1,labelFor(node),p.ink);pen.text(33,1,'---',p.dim);pen.text(50,1,'D--',p.dim);
 pen.text(24,27,'WAIT',p.ink);pen.text(2,52,'NO DATA',p.dim);pen.text(38,52,'NR-:--',p.dim);
 pen.text(2,58,'ALT ?',p.dim);pen.text(48,58,'BAT?',p.dim);return output;
}
