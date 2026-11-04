import {chooseVariant} from './variants.mjs';
import {coordinationFrame} from './coordination.mjs';
import {stateDuration} from './renderer.mjs';
import {pingPong,visualPhase} from './playback.mjs';

function hash(seed,a,b=0){let n=(seed^Math.imul(a+1,0x45d9f3b)^Math.imul(b+1,0x27d4eb2d))>>>0;n=Math.imul(n^(n>>>16),0x45d9f3b);return (n^(n>>>16))>>>0;}
const flightStates=['SCAN','LOITER','SEEN','CHECK','SHARE','LOITER','HOLD','DOUBT'];
export const deploymentDuration=20,searchStart=12+deploymentDuration;
export const endingDuration=outcome=>outcome==='R2B'?22:stateDuration(outcome);
export function endingScene(outcome,age){
 if(age>=endingDuration(outcome))return {state:'BLANK',phase:age-endingDuration(outcome)};
 if(outcome==='R2B')return age<8?{state:'R2B',phase:age}:age<14?{state:'LAND',phase:age-8}:{state:'CHARGE',phase:age-14};
 return {state:outcome,phase:age};
}

// Repeatable visual theatre. No real telemetry, priorities or flight commands.
export function createMission(seed){
 const plans=[],visits=Array.from({length:16},()=>new Map());
 function variantFor(index,state){const occurrence=visits[index].get(state)||0;visits[index].set(state,occurrence+1);return chooseVariant({seed,index,state,occurrence});}
 function plan(number){
  while(plans.length<=number){
   const cycle=plans.length,flightDuration=hash(seed,cycle)%2?96:64;
   const reserveStart=hash(seed,cycle,77)%16,reserves=[reserveStart,(reserveStart+8)%16];
   const participants=Array.from({length:16},(_,i)=>i).filter(i=>!reserves.includes(i));
   const nodes=Array.from({length:16},(_,index)=>{
    const cameraVariant=chooseVariant({seed,index,state:'FLIGHT',occurrence:cycle});
    const segments=[];
    for(let round=0;round<flightDuration/32;round++){
     for(const [slot,start,end] of [[0,0,20]]){
      const state=round===0?(index%2?'LOITER':'SCAN'):flightStates[hash(seed,cycle*97+round*3+slot,index)%flightStates.length];
      segments.push({start:round*32+start,end:round*32+end,state,variant:variantFor(index,state)});
     }
     for(const [start,end] of [[20,22],[22,24],[24,26],[26,30],[30,32]]){
      const story=coordinationFrame(round*12+start-20,0,participants),node=story.nodes[index];
      segments.push({start:round*32+start,end:round*32+end,state:node.state,variant:variantFor(index,node.state),coordination:node});
     }
    }
    let motionEnd=6+deploymentDuration;
    for(const segment of segments){segment.motionStart=motionEnd;motionEnd+=visualPhase(segment.state,segment.end-segment.start);}
    const draw=hash(seed,cycle*17+index,271)%10,outcome=draw<3?'ZOOM':draw<5?'CRASH':draw<6?'EMPTY':'R2B';
    return {cameraVariant,segments,motionEnd,reserve:reserves.includes(index),outcome,outcomeVariant:variantFor(index,outcome),delay:hash(seed,cycle,index)%5};
   });
   const terminalDuration=Math.max(...nodes.filter(n=>!n.reserve).map(n=>n.delay+endingDuration(n.outcome)));
   const previous=plans.at(-1),start=previous?previous.start+previous.duration:0;
   plans.push({cycle,start,flightDuration,terminalDuration,duration:searchStart+flightDuration+terminalDuration+5,nodes,participants});
  }
  return plans[number];
 }
 function frame(time){
  time=Math.max(0,time);let cycle=0,current=plan(0);
  while(time>=current.start+current.duration)current=plan(++cycle);
  const elapsed=time-current.start,flightTime=elapsed-searchStart,terminalStart=searchStart+current.flightDuration,gapStart=terminalStart+current.terminalDuration;
  const stage=elapsed<2?'APPROVED':elapsed<6?'ORDERS':elapsed<12?'TAKEOFF':elapsed<searchStart?'DEPLOY':elapsed<terminalStart?'FLIGHT':elapsed<gapStart?'ENDING':'GAP';
  let communications=Array(16).fill(null);
  const nodes=current.nodes.map((node,index)=>{
   let state,phase,variant=node.cameraVariant,coordination=null,motionTime=elapsed-6,sensor='night';
   if(stage==='APPROVED'){state='APPROVED';phase=elapsed;}
   else if(stage==='ORDERS'){state='ORDERS';phase=elapsed-2;}
   else if(stage==='TAKEOFF'){state='TAKEOFF';phase=elapsed-6;sensor='cam';}
   else if(stage==='DEPLOY'){state='DEPLOY';phase=elapsed-12;sensor='cam';}
   else if(stage==='FLIGHT'){
    const segment=node.segments.find(s=>flightTime>=s.start&&flightTime<s.end);
    ({state,variant,coordination=null}=segment);phase=flightTime-segment.start;
    motionTime=segment.motionStart+visualPhase(state,phase);
    sensor=['cam','whitehot','blackhot','night'][(index+cycle+Math.floor(flightTime/5))%4];
   }else if(stage==='ENDING'){
    const age=elapsed-terminalStart-node.delay;
    if(age<0){state='SCAN';phase=0;}else ({state,phase}=endingScene(node.outcome,age));
    variant=age<0?node.cameraVariant:node.outcomeVariant;
    if(age<0){phase=elapsed-terminalStart;motionTime=node.motionEnd+pingPong(phase);}
    else motionTime=node.motionEnd+pingPong(node.delay)+age;
   }else {state='BLANK';phase=elapsed-gapStart;}
   const launch=Math.max(0,Math.min(1,(elapsed-6)/6)),smooth=launch*launch*(3-2*launch),landingAltitude=40+index%5*3;
   const descent=Math.min(1,Math.max(0,phase/6)),landEase=descent*descent*(3-2*descent);
   let altitude=Math.round(landingAltitude*smooth);
   if(state==='LAND')altitude=Math.round(landingAltitude*(1-landEase));
   if(state==='CHARGE')altitude=0;
   if(node.reserve&&stage!=='GAP'){state='STANDBY';phase=elapsed;altitude=0;sensor='night';coordination=null;}
   return {state,phase,variant,coordination,sensor,camera:{time:elapsed-6,motionTime,variant:node.cameraVariant,launch:smooth,altitude,landingAltitude,observationsEnabled:stage==='FLIGHT'&&flightTime>=4&&!node.reserve},mission:cycle+1};
  });
  if(stage==='FLIGHT'){
   const round=Math.floor(flightTime/32),offset=flightTime%32;
   if(offset>=20)communications=coordinationFrame(round*12+offset-20,0,current.participants).communications;
   else{
    const age=flightTime%2,slot=Math.floor(flightTime/2);
    const sender=Array.from({length:16},(_,i)=>(slot+i)%16).find(i=>nodes[i].state==='SHARE');
    if(sender!==undefined&&age<.625){const receiver=current.participants[(current.participants.indexOf(sender)+5)%current.participants.length];communications[sender]={direction:'TX',peer:receiver,age};communications[receiver]={direction:'RX',peer:sender,age};}
   }
   // Fixed friendly-report fixture: all displays reference the same report,
   // independent of their current state, sensor view or reversing animation.
   if(offset>=12&&offset<16){
    const source=current.participants[(round*3)%current.participants.length],age=offset-12;
    communications=Array(16).fill(null);
    for(let index=0;index<16;index++){
     nodes[index].designation={kind:'friendly',x:20,y:28,source,age};
     if(age<.625)communications[index]={direction:index===source?'TX':'RX',peer:index===source?'ALL':source,age};
    }
   }
  }
  return {stage,cycle,elapsed,nodes,communications,plan:current,remaining:current.duration-elapsed};
 }
 return {plan,frame};
}
