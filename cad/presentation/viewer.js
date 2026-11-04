import * as T from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {GLTFExporter} from './vendor/GLTFExporter.js';
const cfg=await (await fetch('./assembly.json')).json();
const scene=new T.Scene(),model=new T.Group();model.name='Flockinator_Concept_mm_to_m';scene.add(model);
const camera=new T.PerspectiveCamera(34,innerWidth/innerHeight,.01,20);
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(innerWidth,innerHeight);renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1;document.body.prepend(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=.2;controls.maxDistance=4;
const groups=cfg.group_names.map(name=>{const g=new T.Group();g.name=name;model.add(g);return g;});
const mat=(color,roughness=.7,metalness=0)=>new T.MeshStandardMaterial({color,roughness,metalness});
const mats={backing:mat('#b9aa8c'),structure:mat('#dedfda'),carrier:mat('#373e39'),panel:mat('#1b221f'),trim:mat('#ebece5'),controller:mat('#236653'),speaker:mat('#202826'),channel_body:mat('#e2e5de'),connector:mat('#444943'),console:mat('#efeee6'),console_screen:mat('#dedfd6'),power_enclosure:mat('#858e88',.5,.35),power_door:mat('#a3aaa5',.55,.25),timber_foot:mat('#f0f0e9')};
const screens=[],skins=[],trims=[],links=[];const unitBox=new T.BoxGeometry(1,1,1);
function texture(canvas){let t=new T.CanvasTexture(canvas);t.colorSpace=T.SRGBColorSpace;t.anisotropy=renderer.capabilities.getMaxAnisotropy();return t;}
function canvas(w,h=w){const c=document.createElement('canvas');c.width=w;c.height=h;return c;}
// Each face is drawn from exactly 64 x 64 logical pixels. No coarsened display grid.
function pixelTextures(id){const c=canvas(768),e=canvas(768);const a=c.getContext('2d'),b=e.getContext('2d');a.fillStyle='#3b4540';a.fillRect(0,0,768,768);b.fillStyle='#000';b.fillRect(0,0,768,768);
 const rogue=id===6, affected=[5,9,10].includes(id),rgb=rogue?[244,91,129]:affected?[246,175,68]:[55,194,185];
 const number=canvas(64);const n=number.getContext('2d');n.font='bold 9px monospace';n.fillStyle='white';n.fillText(String(id+1).padStart(2,'0'),4,12);n.font='6px monospace';n.fillText(rogue?'UNCERTAIN':affected?'ASSESSING':'LISTENING',4,59);const label=n.getImageData(0,0,64,64).data;
 for(let y=0;y<64;y++)for(let x=0;x<64;x++){
   const dx=x-31.5,dy=y-31,r=Math.hypot(dx,dy),ang=Math.atan2(dy,dx),wave=Math.sin(x*.18+y*.13+id*.7);
   let active=(r>14&&r<16.3)||(Math.abs(dx)<1.2&&Math.abs(dy)<10)||(Math.abs(dy)<1.2&&Math.abs(dx)<10);
   if(rogue)active=(Math.abs(dx-dy)<1.2||Math.abs(dx+dy)<1.2)&&r<16;
   if(affected)active=(r>13&&r<16)&&(Math.sin(ang*4+id)>.05);
   if(label[(y*64+x)*4+3]>100)active=true;
   let q=active?1:((r<23&&wave>.77)?.18:0);
   a.fillStyle=q?`rgb(${rgb.map(v=>Math.round(225*(1-q)+(v*.75+45)*q)).join(',')})`:'#e1e7df';a.fillRect(x*12+1,y*12+1,10,10);
   if(q){b.fillStyle=`rgb(${rgb.map(v=>Math.round(v*q)).join(',')})`;b.fillRect(x*12+1,y*12+1,10,10);}
 }
 const off=canvas(768),oc=off.getContext('2d');oc.fillStyle='#3b4540';oc.fillRect(0,0,768,768);oc.fillStyle='#e1e7df';for(let yy=0;yy<64;yy++)for(let xx=0;xx<64;xx++)oc.fillRect(xx*12+1,yy*12+1,10,10);return [texture(c),texture(e),texture(off)];}
// Global hex coordinates keep the motif in phase across rail and quadrant seams.
function hexTexture(part){const [w,h]=part.size;const c=canvas(Math.max(32,Math.round(w*5)),Math.max(32,Math.round(h*5)));const a=c.getContext('2d');a.fillStyle='#edf0e8';a.fillRect(0,0,c.width,c.height);a.strokeStyle='#b5c2b4';a.lineWidth=.38;
 a.scale(c.width/w,c.height/h);const xmin=part.center[0]-w/2,ymax=part.center[1]+h/2;const rad=3.6,dy=Math.sqrt(3)*rad;
 for(let col=-90;col<=90;col++)for(let row=-80;row<=80;row++){
 const x=col*rad*1.5,y=row*dy+(col%2)*dy/2;if(x<xmin-rad||x>xmin+w+rad||y>ymax+dy||y<ymax-h-dy)continue;
 a.beginPath();for(let k=0;k<6;k++){let xx=x+rad*Math.cos(k*Math.PI/3)-xmin,yy=ymax-(y+rad*Math.sin(k*Math.PI/3));k?a.lineTo(xx,yy):a.moveTo(xx,yy);}a.closePath();a.stroke();}
 return texture(c);}
function shapeFor(p){const sh=new T.Shape(p.outline.map(([x,y])=>new T.Vector2(x/1000,y/1000)));for(const points of p.holes){sh.holes.push(new T.Path(points.map(([x,y])=>new T.Vector2(x/1000,y/1000))));}return sh;}
function shapeGeometry(p,flat=false){const shape=shapeFor(p);const g=flat?new T.ShapeGeometry(shape):new T.ExtrudeGeometry(shape,{depth:p.size[2]/1000,bevelEnabled:false,steps:1});if(!flat)g.translate(0,0,-p.size[2]/2000);const positions=g.attributes.position,uv=g.attributes.uv;for(let i=0;i<uv.count;i++)uv.setXY(i,positions.getX(i)/(p.size[0]/1000)+.5,positions.getY(i)/(p.size[1]/1000)+.5);return g;}
const ec=canvas(1024),ect=ec.getContext('2d');const emap=texture(ec);
function drawEmission(time=0){ect.fillStyle='#060a08';ect.fillRect(0,0,1024,1024);const scale=1024/835.8;ect.save();ect.translate(512,512);ect.scale(scale,-scale);ect.lineWidth=35.8;ect.lineJoin='round';ect.strokeStyle='#469f8e';ect.beginPath();ect.moveTo(-200,0);ect.lineTo(200,0);ect.lineTo(200,200);ect.moveTo(0,0);ect.lineTo(0,200);ect.stroke();ect.strokeStyle='#c68758';ect.beginPath();ect.moveTo(0,200);ect.lineTo(200,200);ect.stroke();if(animation){ect.fillStyle='#c5ffe0';let t=((time*85)%400)-200;ect.fillRect(t-15,-17.9,30,35.8);}ect.restore();emap.needsUpdate=true;}
let pi=0;
for(const p of cfg.parts){let material=mats[p.role]||mat('#fff');let geo=p.outline?shapeGeometry(p):unitBox;
 if(p.role==='pixel_face'){const [map,em,off]=pixelTextures(pi++);material=new T.MeshStandardMaterial({map,emissiveMap:em,emissive:'#ffffff',emissiveIntensity:1,roughness:.8});material.onMap=map;material.offMap=off;screens.push(material);}
 const o=new T.Mesh(geo,p.role==='pixel_face'?[mats.trim,mats.trim,mats.trim,mats.trim,material,mats.panel]:material);o.name=p.name;o.position.fromArray(p.center.map(x=>x/1000));if(!p.outline)o.scale.fromArray(p.size.map(x=>x/1000));o.castShadow=true;o.receiveShadow=true;groups[p.module].add(o);
 if(p.role==='trim')trims.push(o);
 if(p.role==='channel_skin'){
  const tex=hexTexture(p);const sm=new T.MeshStandardMaterial({map:tex,roughness:.85,emissive:'#ffffff',emissiveMap:emap,emissiveIntensity:.04});
  const face=new T.Mesh(shapeGeometry(p,true),sm);face.name=p.name+'_hex_surface';face.position.set(p.center[0]/1000,p.center[1]/1000,(p.center[2]+p.size[2]/2+.03)/1000);groups[p.module].add(face);skins.push({mat:sm,part:p});
 }
}
// Console screen content, legible as a separate control instrument.
const cc=canvas(640,352),ct=cc.getContext('2d');ct.fillStyle='#e4e8d9';ct.fillRect(0,0,640,352);ct.fillStyle='#25392f';ct.font='bold 38px monospace';ct.fillText('FLOCKINATOR',32,58);ct.font='22px monospace';ct.fillText('16 NODES / RUN 004',32,99);for(let i=0;i<16;i++){ct.fillStyle=i===6?'#7b826d':'#354d40';ct.fillRect(35+(i%8)*72,140+Math.floor(i/8)*67,52,47);}ct.fillStyle='#25392f';ct.font='22px monospace';ct.fillText('MONITOR     DEPLOY     RESET',32,320);let cm=new T.Mesh(new T.PlaneGeometry(.12,.066),new T.MeshStandardMaterial({map:texture(cc),roughness:.85}));cm.position.set(.590,-.430,.13055);groups[3].add(cm);
// Rear harness is conceptual routing, not an electrical wiring diagram.
function cable(points,color,module,r=.002){const path=new T.CatmullRomCurve3(points.map(p=>new T.Vector3(...p)));const m=new T.Mesh(new T.TubeGeometry(path,32,r,6,false),mat(color));m.name='Illustrative_rear_harness';groups[module].add(m);}
for(let row=0;row<4;row++)for(let col=0;col<4;col++){const x=-.3+col*.2,y=.3-row*.2;cable([[0,-.32,-.019],[0,y,-.02],[x,y,-.022]],col%2?'#b65f4e':'#333d39',0);}
const ambient=new T.HemisphereLight('#f2f8ff','#7c857c',2);scene.add(ambient);
function light(color,intensity,pos,size){const l=new T.DirectionalLight(color,intensity);l.position.set(...pos);l.castShadow=true;l.shadow.mapSize.set(2048,2048);l.shadow.camera.left=-1.5;l.shadow.camera.right=1.5;l.shadow.camera.top=1.5;l.shadow.camera.bottom=-1.5;l.shadow.normalBias=.001;l.shadow.bias=-.00015;scene.add(l);return l;}
const key=light('#fff8e6',3,[-1,2,2]),fill=light('#cbdffa',1,[2,.8,1]);fill.castShadow=false;
const floor=new T.Mesh(new T.PlaneGeometry(200,200),mat('#e0e4df',.9));floor.rotation.x=-Math.PI/2;floor.position.y=-.48;floor.receiveShadow=true;scene.add(floor);
const glow=new T.PointLight('#70c6b3',.06,1.5,2);glow.position.set(0,0,.18);scene.add(glow);
const captions={hero:['Rounded hive / rigid assembly','One rigid frame on white timber feet, with a separate handheld remote. Rear power enclosure shown as a placement study.'],front:['Front elevation / 875.8 mm square body','Rounded track corners and continuous honeycomb pattern. The handheld controller is shown beside the display.'],side:['Organic track profile / oblique view','Broad outer curves soften the grid. Full 64 × 64 panel faces remain square and individually serviceable.'],rear:['Rear service concept / one rigid backing','300 × 300 × 150 mm steel enclosure mounted low. Feet, clearance, heat rejection and mounting loads require validation.'],remote:['LilyGo / handheld remote','Separate battery-powered status and management controller. Case, battery volume and screen dimensions are provisional.'],detail:['Node and honeycomb detail','Native 64 × 64 pixels with fine rounded aperture corners. Continuous honeycomb styling belongs to the communication tracks.'],corner:['Rounded track corner / honeycomb','35.8 mm outer track radius and 45 mm backing radius. Custom concept geometry, not a verified purchased-tile adaptation.']};
let lighting='day',view='hero',animation=false;
function updateCaption(){const lights={day:'conference daylight',warm:'warm interior',dim:'dim exhibition',off:'daylight / LEDs off'};document.querySelector('#caption').textContent=captions[view][0].split(' / ')[0]+' / '+lights[lighting];}
function setLighting(mode){lighting=mode;const dark=mode==='dim';document.body.classList.toggle('dark',dark);scene.background=new T.Color(dark?'#111b20':mode==='warm'?'#ded6c7':'#e8ebe6');floor.material.color.set(dark?'#111b20':mode==='warm'?'#d2c7b4':'#dce2db');ambient.intensity=dark?.08:mode==='warm'?.7:1.6;key.intensity=dark?.12:mode==='warm'?1.8:2.5;fill.intensity=dark?.07:.7;key.color.set(mode==='warm'?'#ffc685':'#fff6e4');screens.forEach(m=>m.emissiveIntensity=mode==='off'?0:dark?1.1:.65);screens.forEach(m=>{m.map=mode==='off'?m.offMap:m.onMap;m.needsUpdate=true;});glow.intensity=dark?.09:0;updateRails(0);document.querySelector('#light').value=mode;updateCaption();}
function updateRails(time){drawEmission(time);for(const s of skins)s.mat.emissiveIntensity=lighting==='off'?0:lighting==='dim'?1.1:.45;}
function setTrim(v){mats.trim.color.set(v==='black'?'#252e29':'#ebece5');document.querySelector('#trim').value=v;}
function setView(v){view=v;const poses={hero:[[1.25,.67,2.02],[.07,0,0]],front:[[.065,0,2.3],[.065,0,0]],side:[[2.05,.44,1.22],[.08,0,0]],rear:[[-1.12,.5,-1.85],[.04,0,0]],remote:[[.83,-.28,.59],[.55,-.41,.10]],detail:[[.42,.4,.69],[.1,.13,.06]],corner:[[-.75,.72,.71],[-.31,.30,.06]]};camera.position.fromArray(poses[v][0]);controls.target.fromArray(poses[v][1]);controls.update();document.querySelector('#view').value=v;document.querySelector('#description').textContent=captions[v][1];updateCaption();}
async function exportGLB(){let exporter=new GLTFExporter();return await exporter.parseAsync(model,{binary:true,onlyVisible:true});}
window.presentation={setLighting,setView,setTrim,exportGLB,scene,model,camera,renderer,config:cfg,ready:true,render:()=>renderer.render(scene,camera)};
for(const [id,fn] of [['light',setLighting],['view',setView],['trim',setTrim]])document.getElementById(id).onchange=e=>fn(e.target.value);
document.getElementById('motion').onclick=()=>{animation=!animation;document.getElementById('motion').textContent=animation?'Pause communication preview':'Play communication preview';};
document.getElementById('download').onclick=async()=>{let blob=new Blob([await exportGLB()],{type:'model/gltf-binary'});let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='Flockinator-concept.glb';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
if(new URLSearchParams(location.search).has('render'))document.body.classList.add('render');
setView('hero');setLighting('day');
window.addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});
renderer.setAnimationLoop(t=>{controls.update();if(animation)updateRails(t/1000);renderer.render(scene,camera);});
