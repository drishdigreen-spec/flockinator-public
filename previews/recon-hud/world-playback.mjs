import {validateSnapshot} from './world-view.mjs';
const clamp=n=>Math.max(0,Math.min(1,n));
const wrap=n=>((n%360)+360)%360;
const angle=(a,b,t)=>wrap(a+(((b-a+180)%360+360)%360-180)*t);
function poseBetween(a,b,t){return {position:a.position.map((n,i)=>n+(b.position[i]-n)*t),heading:angle(a.heading,b.heading,t),pitch:a.pitch+(b.pitch-a.pitch)*t,roll:angle(a.roll,b.roll,t)};}
export function createWorldPlayback({delayMs=500,staleMs=1500,resyncMs=750}={}){
 if(![delayMs,staleMs,resyncMs].every(Number.isFinite)||delayMs<0||staleMs<=0||resyncMs<=0)throw new TypeError('Invalid playback timing');
 let samples=[],received=null,transition=null,lastPresented=null,rejected=0;
 function receive(snapshot,receiptMs,{reset=false}={}){
  const last=samples.at(-1),bad=validateSnapshot(snapshot)||!Number.isFinite(receiptMs)||receiptMs<0;
  if(bad||(!reset&&last&&(snapshot.node!==last.node||snapshot.run!==last.run||snapshot.seq<=last.seq||snapshot.timeMs<=last.timeMs||receiptMs<received))){rejected++;return false;}
  const reconnect=!reset&&last&&receiptMs-received>=staleMs;
  if(reset){samples=[];transition=null;lastPresented=null;rejected=0;}
  if(reconnect){transition={from:structuredClone(lastPresented??last.pose),start:receiptMs};samples=[];}
  samples.push(structuredClone(snapshot));samples=samples.slice(-4);received=receiptMs;return true;
 }
 function sample(nowMs){
  if(!Number.isFinite(nowMs)||nowMs<0)throw new TypeError('Invalid presentation clock');
  if(!samples.length)return {snapshot:null,status:'WAIT',ageMs:null,rejected};
  const desired=nowMs-delayMs;
  let a=samples[0],b=a;
  for(const entry of samples){if(entry.timeMs<=desired)a=entry;else {b=entry;break;}b=a;}
  const t=a===b?0:clamp((desired-a.timeMs)/(b.timeMs-a.timeMs));
  const snapshot=structuredClone(t===1?b:a);
  snapshot.pose=poseBetween(a.pose,b.pose,t);snapshot.timeMs=a.timeMs+(b.timeMs-a.timeMs)*t;
  if(a.effectAgeMs!==undefined&&b.effectAgeMs!==undefined)snapshot.effectAgeMs=a.effectAgeMs+(b.effectAgeMs-a.effectAgeMs)*t;
  for(const key of ['peers','observations'])snapshot[key]=snapshot[key].map(p=>{
   const next=b[key].find(q=>q.id===p.id);
   return next?{...p,position:p.position.map((n,i)=>n+(next.position[i]-n)*t)}:p;
  });
  const ageMs=Math.max(0,nowMs-received);let status=ageMs>=staleMs?'STALE':'LIVE';
  if(transition){const fraction=clamp((nowMs-transition.start)/resyncMs);snapshot.pose=poseBetween(transition.from,snapshot.pose,fraction);if(status==='LIVE'&&fraction<1)status='RESYNC';if(fraction===1)transition=null;}
  if(status==='STALE'){snapshot.peers=[];snapshot.observations=[];}
  lastPresented=structuredClone(snapshot.pose);
  return {snapshot,status,ageMs,rejected};
 }
 return {receive,sample};
}
// Authored visual effect: captures a displayed pose, then pitches/rolls into dirt.
// No dynamics, collision detection, navigation or real-world flight model.
export function impactSnapshot(entry,startMs,nowMs){
 const error=validateSnapshot(entry);if(error)throw new TypeError(error);
 if(!Number.isFinite(startMs)||!Number.isFinite(nowMs)||startMs<0||nowMs<startMs)throw new TypeError('Invalid impact clock');
 const age=nowMs-startMs,t=clamp(age/2000),ease=t*t*(3-2*t),pose=structuredClone(entry.pose);
 pose.position[2]+=(.25-pose.position[2])*ease;pose.pitch+=(-90-pose.pitch)*ease;pose.roll+=(entry.node%2?-180:180)*ease;
 const stage=age<2000?'impact':age>=3000&&age<8000?'static':'ground';
 return {...entry,timeMs:nowMs,pose,stage,effectAgeMs:age,label:stage==='impact'?'IMPACT':stage==='static'?'NO LINK':'GROUND',peers:[],observations:[]};
}
