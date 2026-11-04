// Exhibition game geometry and energy points. No aircraft/weapon performance model.
export const VERSION='survey-2';
export const scenario=Object.freeze({version:1,tickMs:100,seed:271828,speed:10,altitude:24,takeoffTicks:40,landTicks:40,surveyTicks:300,drain:8,charge:25,reserve:2500,sites:[[0,150,24],[-100,220,24],[120,200,24]],maxTicks:360000});
export const states=['READY','TAKEOFF','TRANSIT','SURVEY','RETURN','LAND','CHARGING','UNAVAILABLE'];
const airborne=n=>['TAKEOFF','TRANSIT','SURVEY','RETURN','LAND'].includes(n.state);
const wrap=n=>((n%360)+360)%360;
const clone=s=>structuredClone(s);
const distance=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
export function createState(run){
 if(!Number.isInteger(run)||run<1||run>0xffffffff)throw Error('Invalid session');
 return {version:VERSION,run,tick:0,paused:false,limit:false,events:[],nodes:Array.from({length:16},(_,id)=>{
  const home=[(id-7.5)*20,0,.25];return {id,home,pose:{position:[...home],heading:0,pitch:-5,roll:0},energy:10000,state:'READY',reason:'INITIAL',site:null,entered:0,entry:[...home]};
 })};
}
function transition(s,n,state,reason){
 n.state=state;n.reason=reason;n.entered=s.tick;n.entry=[...n.pose.position];n.entryHeading=n.pose.heading;n.entryPitch=n.pose.pitch;n.entryRoll=n.pose.roll;
 s.events.push({tick:s.tick,node:n.id,state,reason});
}
export function command(state,c){
 if(!c||typeof c!=='object'||Array.isArray(c)||!['launch','return','pause','resume','unavailable'].includes(c.op))throw Error('Invalid operation');
 if(Object.keys(c).some(k=>!['op','nodes','site'].includes(k)))throw Error('Unknown command field');
 if(['pause','resume'].includes(c.op)){const s=clone(state);if(s.limit&&c.op==='resume')throw Error('Session limit: export and reset');s.paused=c.op==='pause';return s;}
 if(!Array.isArray(c.nodes)||!c.nodes.length||c.nodes.length>16||new Set(c.nodes).size!==c.nodes.length||c.nodes.some(id=>!Number.isInteger(id)||id<0||id>=16))throw Error('Invalid selection');
 if(c.op==='launch'&&(!Number.isInteger(c.site)||c.site<0||c.site>=scenario.sites.length||c.nodes.some(id=>state.nodes[id].state!=='READY')))throw Error('Selection not ready or invalid site');
 if(state.limit)throw Error('Session limit: export and reset');
 const s=clone(state);
 for(const id of c.nodes){const n=s.nodes[id];
  if(c.op==='launch'){n.site=c.site;transition(s,n,'TAKEOFF','SELECTED');}
  else if(c.op==='return'&&airborne(n)&&!['RETURN','LAND'].includes(n.state))transition(s,n,'RETURN','PRESENTER_RETURN');
  else if(c.op==='unavailable'&&n.state!=='UNAVAILABLE')transition(s,n,'UNAVAILABLE','SCENARIO_EVENT');
 }
 return s;
}
function travel(n,destination){
 const p=n.pose.position,dist=distance(p,destination),step=scenario.speed*scenario.tickMs/1000;
 const dx=destination[0]-p[0],dy=destination[1]-p[1];
 if(Math.abs(dx)+Math.abs(dy)>.001){const heading=wrap(Math.atan2(dx,dy)*180/Math.PI),delta=wrap(heading-n.pose.heading+180)-180;n.pose.heading=wrap(n.pose.heading+Math.max(-8,Math.min(8,delta)));}
 n.pose.pitch=-5;n.pose.roll=0;
 n.pose.position=dist<=step?[...destination]:p.map((v,i)=>v+(destination[i]-v)*step/dist);
 return dist<=step;
}
export function advance(state,ticks){
 if(!Number.isInteger(ticks)||ticks<0||ticks>10000)throw Error('Invalid tick count');
 const s=clone(state);if(s.paused)return s;
 for(let i=0;i<ticks;i++){
  if(s.tick>=scenario.maxTicks||s.events.length>=20000){s.paused=true;s.limit=true;break;}
  s.tick++;
  for(const n of s.nodes){
   if(airborne(n)){
    n.energy=Math.max(0,n.energy-scenario.drain);
    if(n.energy===0){transition(s,n,'UNAVAILABLE','ENERGY_EMPTY');continue;}
    if(n.energy<=scenario.reserve&&!['RETURN','LAND'].includes(n.state))transition(s,n,'RETURN','GAME_RESERVE');
   }
   const age=s.tick-n.entered;
   if(n.state==='TAKEOFF'){
    const t=Math.min(1,age/scenario.takeoffTicks);n.pose.position=[n.home[0],n.home[1],n.home[2]+(scenario.altitude-n.home[2])*t];
    if(t===1)transition(s,n,'TRANSIT','AIRBORNE');
   }else if(n.state==='TRANSIT'){
    if(travel(n,scenario.sites[n.site]))transition(s,n,'SURVEY','AT_SITE');
   }else if(n.state==='SURVEY'){
    // A small closed observation orbit starts at the exact arrival position.
    const a=age*.01,site=scenario.sites[n.site];n.pose.position=[site[0]+12*(1-Math.cos(a)),site[1]+12*Math.sin(a),scenario.altitude];
    n.pose.heading=wrap(n.entryHeading+a*180/Math.PI);const blend=Math.min(1,age/20);n.pose.pitch=n.entryPitch+(-12-n.entryPitch)*blend;n.pose.roll=n.entryRoll+(5-n.entryRoll)*blend;
    if(age>=scenario.surveyTicks)transition(s,n,'RETURN','SURVEY_COMPLETE');
   }else if(n.state==='RETURN'){
    if(travel(n,[n.home[0],n.home[1],Math.max(.25,n.entry[2])]))transition(s,n,'LAND','AT_HOME');
   }else if(n.state==='LAND'){
    const t=Math.min(1,age/scenario.landTicks);n.pose.position=n.entry.map((v,j)=>v+(n.home[j]-v)*t);
    if(t===1)transition(s,n,'CHARGING','LANDED');
   }else if(n.state==='CHARGING'){
    n.energy=Math.min(10000,n.energy+scenario.charge);
    if(n.energy===10000){n.site=null;transition(s,n,'READY','CHARGED');}
   }
  }
 }
 return s;
}
export function snapshot(s,id,seq){
 if(!Number.isInteger(id)||id<0||id>=16)throw Error('Invalid node');
 const n=s.nodes[id],destination=['RETURN','LAND'].includes(n.state)?n.home:n.site===null?null:scenario.sites[n.site];
 return {version:2,run:s.run,seq,timeMs:s.tick*scenario.tickMs,seed:scenario.seed,node:id,pose:clone(n.pose),state:n.state,reason:n.reason,paused:s.paused,energy:n.energy,distance:destination?distance(n.pose.position,destination):null,reserve:['RETURN','LAND'].includes(n.state)?2:n.energy<=scenario.reserve?1:0,peers:s.nodes.filter(p=>p.id!==id&&airborne(p)).map(p=>({id:p.id,position:[...p.pose.position],observedMs:s.tick*scenario.tickMs}))};
}
export function wireSnapshot(s,id,seq){
 const v=snapshot(s,id,seq),p=v.pose;
 return {op:'display_survey',v:2,run:v.run,seq,t:v.timeMs,n:id,p:[...p.position,p.heading,p.pitch,p.roll].map(x=>Math.round(x*10)),e:v.energy,d:v.distance===null?-1:Math.round(v.distance),s:states.indexOf(v.state),r:v.reserve,q:v.peers.slice(0,3).map(p=>[p.id,...p.position.map(x=>Math.round(x*10))])};
}
