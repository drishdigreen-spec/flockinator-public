import {mapSnapshot,drawMap,installFullscreen,observeMapSize} from './mission-map.mjs';
import {missionWorld,renderMissionView,airborne} from './mission-world.mjs';
import {renderWorldView,renderWorldWaiting,layoutSightings} from './world-view.mjs';
import {createWorldStream} from './world-fixture.mjs';
import {sampleReadouts,distanceLabel,returnLabel} from './readouts.mjs';
import {createMission} from './mission.mjs';
import {coordinationFrame} from './coordination.mjs';
import {variants,chooseVariant} from './variants.mjs';
import {communicationFrame} from './communication.mjs';
import {renderHUD,states,stateLabel,sceneAt,stateDuration,sequenceDuration,labelFor,peerLabel,descriptions,sensorViews} from './renderer.mjs';
const sessionSeed=crypto.getRandomValues(new Uint32Array(1))[0];
const missionPlayer=createMission(sessionSeed);
const $=id=>document.getElementById(id),array=$('array'),focus=$('focus').getContext('2d');
let selected=0,time=0,sceneStarted=0,playing=!matchMedia('(prefers-reduced-motion: reduce)').matches,previous=performance.now(),lastDraw=0;
const tiles=Array.from({length:16},(_,index)=>{const button=document.createElement('button');button.className='node';button.setAttribute('aria-label',`Inspect ${labelFor(index)}`);button.setAttribute('aria-pressed',String(index===0));const canvas=document.createElement('canvas');canvas.width=canvas.height=64;canvas.setAttribute('aria-hidden','true');button.append(canvas);array.append(button);button.addEventListener('click',()=>{selected=index;tiles.forEach((tile,i)=>tile.button.setAttribute('aria-pressed',String(i===index)));draw();});return {button,ctx:canvas.getContext('2d')};});
const summaries=['Await order','Survey the site','Observe contacts','Share report','Seek evidence','Conflicting claims','Target engaged','Target lost','Countdown → static','Crash → static','Battery depleted','Contact lost','Broadcast alert','Preset priority','Competing claims','Observation owner','Release claim','Orbit or grid','Return home','Controlled descent','Recharge on pad','Reserve node','Friendly broadcast','Confirmed target','Outbound deployment'];
states.forEach((state,i)=>{if(i>=6){const option=document.createElement('option');option.value=state;option.textContent=stateLabel(state);$('scene').append(option);}const b=document.createElement('button');b.textContent=String(i+1).padStart(2,'0')+' / '+stateLabel(state);b.setAttribute('aria-pressed','false');const small=document.createElement('small');small.textContent=summaries[i];b.append(small);b.addEventListener('click',()=>{$('scene').value=state;sceneStarted=time;draw();});$('beats').append(b);});
variants.forEach((variant,index)=>{const option=document.createElement('option');option.value=String(index);option.textContent=String(index+1).padStart(2,'0')+' · '+variant.name;$('variant').append(option);});
let worldStream=createWorldStream();
let worldMetrics={batches:[],total:0,missedSlots:0};
function resetWorld(){worldStream=createWorldStream();worldMetrics={batches:[],total:0,missedSlots:0};lastDraw=performance.now();}
const worldClock=()=>Math.max(0,(time-sceneStarted)*1000);
const worldFrames=Array.from({length:16},()=>new ImageData(64,64));
function drawWorld(){
 const started=performance.now();
 const elapsed=worldClock(),samples=worldStream.frame(elapsed),sensor=$('sensor').value==='auto'?'cam':$('sensor').value;
 tiles.forEach((tile,index)=>{
  const {snapshot,status,ageMs}=samples[index];
  if(snapshot)renderWorldView(snapshot,{sensor,palette:$('palette').value,status,output:worldFrames[index].data});
  else renderWorldWaiting(index,{palette:$('palette').value,output:worldFrames[index].data});
  const label=snapshot?.label??'WAIT';
  tile.ctx.putImageData(worldFrames[index],0,0);tile.button.dataset.state=label;tile.button.dataset.sensor=sensor;tile.button.dataset.freshness=status;tile.button.dataset.pose=JSON.stringify(snapshot?.pose??null);tile.button.dataset.stage=snapshot?.stage??'unknown';
  if(index===selected){
   focus.putImageData(worldFrames[index],0,0);$('state').textContent=label;$('source').textContent='Local fixture · '+status.toLowerCase();
   $('description').textContent='Continuous camera pose over shared, seeded terrain. Labels change without rewinding the view. Positions use fictional world units.';
   $('world-pose').textContent=snapshot?'Position '+snapshot.pose.position.map(n=>n.toFixed(1)).join(', ')+' · heading '+snapshot.pose.heading.toFixed(1)+'°':'Waiting for a valid camera pose';
   $('world-freshness').textContent=ageMs===null?'WAIT · no valid snapshot':status+' · sample received '+(ageMs/1000).toFixed(1)+'s ago · 0.5s interpolation delay';
   const sightings=snapshot?layoutSightings(snapshot):{markers:[],omitted:0};
   $('world-sightings').textContent=sightings.markers.length+' peer labels · '+sightings.omitted+' omitted. Cyan IDs are supplied sightings; R means behind. White/black points are neutral landmarks.';
   $('world-toggle').textContent=(worldStream.isEnabled(index)?'Interrupt ':'Resume ')+labelFor(index)+' updates';
   $('world-impact').disabled=status!=='LIVE'||snapshot?.stage!=='air'||!worldStream.isEnabled(index);
   $('focus').setAttribute('aria-label',labelFor(index)+' synthetic world view, '+label+', '+status);
  }
 });
 $('node-title').textContent=labelFor(selected)+' / World view';
 $('clock').textContent=String(Math.floor((time-sceneStarted)/60)).padStart(2,'0')+':'+String(Math.floor((time-sceneStarted)%60)).padStart(2,'0');
 worldMetrics.batches.push(performance.now()-started);if(worldMetrics.batches.length>256)worldMetrics.batches.shift();worldMetrics.total++;
 const sorted=[...worldMetrics.batches].sort((a,b)=>a-b),percentile=p=>sorted[Math.max(0,Math.ceil(sorted.length*p)-1)];
 const metrics={samples:sorted.length,total:worldMetrics.total,elapsedMs:elapsed,p50Ms:percentile(.5),p95Ms:percentile(.95),maxMs:sorted.at(-1),missedSlots:worldMetrics.missedSlots,seed:271828};
 $('world-performance').dataset.metrics=JSON.stringify(metrics);
 $('world-performance').textContent='16-view batches: p50 '+metrics.p50Ms.toFixed(1)+' / p95 '+metrics.p95Ms.toFixed(1)+' / max '+metrics.maxMs.toFixed(1)+' ms · '+metrics.missedSlots+' missed 125ms slots. Latest '+metrics.samples+' batches; browser only.';
}
const mapSession=crypto.randomUUID();
const mapChannel=typeof BroadcastChannel==='function'?new BroadcastChannel('flock-map-'+mapSession):null;
$('map-tab').href='map.html?session='+encodeURIComponent(mapSession);
if(!mapChannel){$('map-tab').hidden=true;$('map-status').textContent='Separate map tabs are unavailable in this browser.';}
installFullscreen($('mission-map-section'),$('map-fullscreen'),$('map-status'));
function advanceClock(now){if(playing)time+=Math.max(0,now-previous)/1000;previous=Math.max(previous,now);}
function currentMap(){
 if($('scene').value!=='mission')return null;
 const mission=missionPlayer.frame(time-sceneStarted);
 return mapSnapshot(mission,missionWorld(mission),selected,playing);
}
if(mapChannel)mapChannel.onmessage=event=>{
 if(event.data?.kind!=='request-map')return;
 advanceClock(performance.now());const snapshot=currentMap();
 mapChannel.postMessage(snapshot??{kind:'map-inactive'});
};
let latestMap=null;
observeMapSize($('mission-map'),()=>latestMap);
function drawMissionMap(mission,frames){
 const snapshot=mapSnapshot(mission,frames,selected,playing);
 latestMap=snapshot;drawMap($('mission-map'),snapshot);
 $('map-status').textContent='Mission '+(mission.cycle+1)+' · '+mission.stage+' · '+(playing?'Playing':'Paused');
}
function draw(){
 const isWorld=$('scene').value==='world';
 $('mission-map-section').hidden=$('scene').value!=='mission';
 $('world-controls').hidden=!isWorld;$('variant').disabled=isWorld;$('world-info').hidden=!isWorld;$('legacy-details').hidden=isWorld;$('legacy-sequence').hidden=isWorld;
 if(isWorld){drawWorld();return;}
 const chosen=$('scene').value,palette=$('palette').value,forced=$('variant').value;
 const mission=chosen==='mission'?missionPlayer.frame(time-sceneStarted):null;
 const sharedWorld=mission?missionWorld(mission):null;
 if(sharedWorld)drawMissionMap(mission,sharedWorld);
 const coordination=chosen==='coordination'?coordinationFrame(time,sceneStarted):null;
 const communications=mission?.communications??coordination?.communications??communicationFrame(time,{scene:chosen,sceneStarted});
 tiles.forEach((tile,index)=>{
  const scene=mission?mission.nodes[index]:coordination?coordination.nodes[index]:chosen==='sequence'?sceneAt(time,index):{state:chosen,phase:(time-sceneStarted)%stateDuration(chosen)};
  const {state,phase}=scene;
  const occurrence=coordination?coordination.cycle:chosen==='sequence'?Math.floor((time+index*2.37)/sequenceDuration):Math.floor((time-sceneStarted)/stateDuration(chosen));
  const variant=forced==='random'?(mission?scene.variant:chooseVariant({seed:sessionSeed,index,state,occurrence})):Number(forced);
  const variantName=String(variant+1).padStart(2,'0')+' / '+variants[variant].name;
  const sensor=$('sensor').value==='auto'?(scene.sensor??'night'):$('sensor').value;
  const designation=scene.designation??(chosen==='FRIEND'?{kind:'friendly',x:20,y:28,source:Math.floor((time-sceneStarted)/2)%16}:null);
  const readouts=sampleReadouts({elapsed:mission?mission.elapsed-6:time-sceneStarted+(state==='TAKEOFF'?0:26),index,state,phase});
  const options={time,index,state,palette,sensor,designation,phase,variant,communication:communications[index],coordination:mission?scene.coordination:coordination?.nodes[index],camera:scene.camera,mission:scene.mission,readouts};
  const data=new ImageData(sharedWorld?renderMissionView(options,sharedWorld[index]):renderHUD(options),64,64);
  tile.button.dataset.pose=JSON.stringify(sharedWorld?.[index].pose??null);
  tile.button.dataset.peers=String(sharedWorld?.[index].peers.length??0);
  tile.ctx.putImageData(data,0,0);tile.button.dataset.variant=String(variant);tile.button.dataset.state=state;tile.button.dataset.sensor=sensor;
  if(index===selected){
   focus.putImageData(data,0,0);$('state').textContent=stateLabel(state);$('description').textContent=descriptions[state]+(designation?' Friendly warning from '+labelFor(designation.source)+': blue pixels mark the reported group.':'');
   $('readout-values').textContent=distanceLabel(readouts.distanceKm)+' · '+returnLabel(readouts.returnSeconds)+' · scripted samples · shared world / cyan peer IDs';
   $('variant-name').textContent=variantName;$('sensor-name').textContent=sensorViews[sensor];
   $('source').textContent=communications[index]?communications[index].direction+' '+peerLabel(communications[index].peer)+' · simulated':mission?'Mission '+(mission.cycle+1)+' · '+mission.stage:'Synthetic mission';
   $('focus').setAttribute('aria-label',`${labelFor(index)} simulated drone camera, ${stateLabel(state)}, variant ${variantName}. ${descriptions[state]} Sensor view: ${sensorViews[sensor]}.`);
  }
 });
 $('node-title').textContent=labelFor(selected)+' / Camera view';
 $('clock').textContent=String(Math.floor(time/60)).padStart(2,'0')+':'+String(Math.floor(time%60)).padStart(2,'0');
 [...$('beats').children].forEach((b,i)=>b.setAttribute('aria-pressed',String(chosen===states[i])));
}
function playLabel(){$('play').textContent=playing?'Pause':'Play';$('play').setAttribute('aria-label',playing?'Pause animation':'Play animation');}
$('play').addEventListener('click',()=>{playing=!playing;previous=performance.now();lastDraw=previous;playLabel();draw();});
$('restart').addEventListener('click',()=>{time=0;sceneStarted=0;resetWorld();if($('scene').value!=='world')$('scene').value='mission';draw();});
$('scene').addEventListener('change',()=>{sceneStarted=time;if($('scene').value==='world')resetWorld();draw();});$('palette').addEventListener('change',draw);$('sensor').addEventListener('change',draw);$('variant').addEventListener('change',draw);$('native').addEventListener('change',()=>{document.body.classList.toggle('native',$('native').checked);});
$('world-toggle').addEventListener('click',()=>{worldStream.setEnabled(selected,!worldStream.isEnabled(selected),worldClock());draw();});
$('world-impact').addEventListener('click',()=>{worldStream.impact(selected,worldClock());draw();});
function tick(now){
 advanceClock(now);
 if(playing&&now-lastDraw>=125){
  const slots=Math.floor((now-lastDraw)/125);
  if($('scene').value==='world'){worldMetrics.missedSlots+=slots-1;lastDraw+=slots*125;}else lastDraw=now;
  draw();
 }
 requestAnimationFrame(tick);
}
playLabel();draw();requestAnimationFrame(tick);
