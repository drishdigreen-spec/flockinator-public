import {validateSnapshot} from './world-view.mjs';
const states=['READY','TAKEOFF','TRANSIT','SURVEY','RETURN','LAND','CHARGING','UNAVAILABLE'];
const wrap=n=>((n%360)+360)%360;
const mix=(a,b,t)=>({position:a.position.map((x,i)=>x+(b.position[i]-x)*t),heading:wrap(a.heading+(wrap(b.heading-a.heading+180)-180)*t),pitch:a.pitch+(b.pitch-a.pitch)*t,roll:wrap(a.roll+(wrap(b.roll-a.roll+180)-180)*t)});
export function createSurveyPlayback(){
 let latest=null,from=null,received=0,blend=500;
 function sample(now){
  if(!latest)return {snapshot:null,status:'WAIT',metrics:null};
  const pose=mix(from,latest.pose,Math.max(0,Math.min(1,(now-received)/blend))),stale=now-received>=2000;
  return {snapshot:{...latest,pose,peers:stale?[]:latest.peers},status:stale?'STALE':latest.paused?'PAUSED':'LIVE',metrics:{energy:latest.energy,distance:latest.distance,reserve:latest.reserve}};
 }
 function receive(v,now){
  if(v?.version!==2||!states.includes(v.state)||!Number.isInteger(v.energy)||v.energy<0||v.energy>10000||!(v.distance===null||Number.isFinite(v.distance)&&v.distance>=0&&v.distance<=99999)||![0,1,2].includes(v.reserve)||typeof v.paused!=='boolean'||!Number.isFinite(now))return false;
  const entry={...v,version:1,label:v.state==='UNAVAILABLE'?'UNAVAIL':v.state,stage:'air',observations:[]};
  if(validateSnapshot(entry)||latest&&(v.run<latest.run||v.node!==latest.node||v.run===latest.run&&(v.seq<=latest.seq||v.timeMs<latest.timeMs)))return false;
  const reset=!latest||latest.run!==v.run;from=reset?structuredClone(v.pose):sample(now).snapshot.pose;
  blend=!reset&&now-received>=2000?750:500;latest=structuredClone(entry);received=now;return true;
 }
 return {receive,sample};
}
