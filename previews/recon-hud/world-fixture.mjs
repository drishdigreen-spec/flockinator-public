import {createWorldPlayback,impactSnapshot} from './world-playback.mjs';
import {validateSnapshot} from './world-view.mjs';
// Authored viewing paths only: no mission planning, sensor decisions or physics.
export function fixturePose(node,timeMs){
 const t=timeMs/1000,angle=t*.025+node*.025,radius=80;
 return {position:[(node%4-1.5)*18+radius*(1-Math.cos(angle)),Math.floor(node/4)*18+radius*Math.sin(angle),20+Math.floor(node/4)*3+Math.sin(t*.15+node)*2],heading:angle*180/Math.PI,pitch:-5+Math.sin(t*.12+node)*2,roll:Math.sin(t*.25+node*.3)*8};
}
export function fixtureSnapshot(node,timeMs,{seed=271828,run=1,seq=Math.floor(timeMs/500)}={}){
 const peers=Array.from({length:16},(_,id)=>({id,position:fixturePose(id,timeMs).position,observedMs:timeMs})).filter(p=>p.id!==node);
 const observations=[[0,100,0],[40,160,0],[-30,180,0]].map((position,id)=>({id,position,observedMs:timeMs}));
 const s={version:1,node,run,seq,timeMs,seed,label:['SURVEY','LOITER','SHARE','CHECK'][Math.floor(timeMs/8000)%4],pose:fixturePose(node,timeMs),stage:'air',peers,observations};
 const error=validateSnapshot(s);if(error)throw new TypeError(error);return s;
}

export function createWorldStream(seed=271828){
 const channels=Array.from({length:16},()=>({player:createWorldPlayback(),enabled:true,seq:0,effect:null}));
 let lastTick=-500,lastNow=0;
 function send(node,nowMs,reset=false){
  const c=channels[node];if(!c.enabled)return;
  const s=c.effect?impactSnapshot(c.effect.entry,c.effect.start,nowMs):fixtureSnapshot(node,nowMs,{seed});
  // Supplied fixture sightings follow the same authored world, including impacts.
  for(const peer of s.peers){const effect=channels[peer.id].effect;if(effect&&nowMs>=effect.start)peer.position=impactSnapshot(effect.entry,effect.start,nowMs).pose.position;}
  s.seq=c.seq++;c.player.receive(s,nowMs,{reset});
 }
 function frame(nowMs){
  if(!Number.isFinite(nowMs)||nowMs<lastNow)throw new TypeError('Restart the stream before rewinding');
  const tick=Math.floor(nowMs/500)*500;
  for(let at=Math.max(lastTick+500,tick-1500);at<=tick;at+=500)for(let node=0;node<16;node++)send(node,at);
  lastTick=tick;lastNow=nowMs;
  return channels.map(c=>c.player.sample(nowMs));
 }
 function channel(node){if(!Number.isInteger(node)||node<0||node>15)throw new TypeError('Invalid node');return channels[node];}
 function setEnabled(node,enabled,nowMs){
  frame(nowMs);const c=channel(node);if(c.enabled===Boolean(enabled))return;c.enabled=Boolean(enabled);if(c.enabled)send(node,nowMs);
 }
 function impact(node,nowMs){
  const current=frame(nowMs)[node],c=channel(node);
  if(!c.enabled||current.status!=='LIVE'||c.effect||!current.snapshot)return false;
  c.effect={entry:structuredClone(current.snapshot),start:nowMs};send(node,nowMs,true);return true;
 }
 return {frame,setEnabled,impact,isEnabled:node=>channel(node).enabled};
}
