import {fixturePose} from './world-fixture.mjs';
import {renderWorldView} from './world-view.mjs';
import {renderHUD} from './renderer.mjs';
const smooth=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
const flightPose=(index,elapsed)=>fixturePose(index,Math.max(0,elapsed-12)*1000);
// Authored camera choreography, not navigation or agent decision logic.
export function missionPose(index,elapsed,scene){
 const {state,phase}=scene,home=flightPose(index,12),pose=flightPose(index,elapsed);
 if(elapsed<12){const u=smooth((elapsed-6)/6);pose.position[2]=.25+(home.position[2]-.25)*u;pose.pitch=-60+(home.pitch+60)*u;pose.roll=home.roll*u;}
 if(state==='R2B'||state==='LAND'){
  const entry=flightPose(index,elapsed-phase-(state==='LAND'?8:0)),u=state==='LAND'?1:smooth(phase/8);
  pose.position=entry.position.map((n,i)=>n+(home.position[i]-n)*u);
  pose.heading=entry.heading+(home.heading-entry.heading)*u;pose.pitch=entry.pitch+(home.pitch-entry.pitch)*u;pose.roll=entry.roll*(1-u);
  if(state==='LAND'){const d=smooth(phase/6);pose.position[2]=home.position[2]+(.25-home.position[2])*d;pose.pitch=home.pitch+(-60-home.pitch)*d;}
 }
 if(['CRASH','EMPTY','NOLINK'].includes(state)){
  Object.assign(pose,flightPose(index,elapsed-phase));
  if(state==='CRASH'){const u=smooth(phase/2);pose.position[2]+=(.25-pose.position[2])*u;pose.pitch+=(-90-pose.pitch)*u;pose.roll+=(index%2?-180:180)*u;}
 }
 if(['STANDBY','CHARGE'].includes(state)){Object.assign(pose,home);pose.position=[home.position[0],home.position[1],.25];pose.pitch=-60;pose.roll=0;}
 return pose;
}
export function airborne(scene){return !['READY','APPROVED','ORDERS','STANDBY','CHARGE','BLANK'].includes(scene.state)&&!(scene.state==='ZOOM'&&scene.phase>=10)&&!(scene.state==='CRASH'&&scene.phase>=2)&&!(scene.state==='EMPTY'&&scene.phase>=3);}
// Reconstruct the last cinematic pose from the plan, not playback history. This
// keeps direct seeks, linked tabs and normal playback identical during the gap.
function presentation(mission,index){
 const scene=mission.nodes[index],plan=mission.plan.nodes[index];
 if(plan.reserve)return {pose:missionPose(index,12,{state:'STANDBY',phase:0}),status:'parked'};
 const duration={ZOOM:10,CRASH:2,EMPTY:3,R2B:14}[plan.outcome];
 const stop=32+mission.plan.flightDuration+plan.delay+duration;
 if(mission.elapsed>=stop){
  const finalScene=plan.outcome==='R2B'?{state:'CHARGE',phase:0}:{state:plan.outcome,phase:duration};
  return {pose:missionPose(index,stop,finalScene),status:plan.outcome==='R2B'?'parked':'lost'};
 }
 return {pose:missionPose(index,mission.elapsed,scene),status:airborne(scene)?'airborne':'parked'};
}
export function missionWorld(mission){
 const timeMs=Math.round(mission.elapsed*1000),views=mission.nodes.map((scene,i)=>presentation(mission,i));
 return mission.nodes.map((scene,node)=>({version:1,node,run:mission.cycle+1,seq:Math.floor(timeMs/125),timeMs,seed:271828,label:'MISSION',pose:views[node].pose,presentationStatus:views[node].status,stage:scene.state==='CRASH'?(scene.phase>=2?'ground':'impact'):'air',effectAgeMs:scene.state==='CRASH'?scene.phase*1000:0,
  peers:mission.nodes.flatMap((peer,id)=>id!==node&&views[id].status==='airborne'?[{id,position:[...views[id].pose.position],observedMs:timeMs}]:[]),observations:[]}));
}
export function renderMissionView(options,snapshot){
 // The original cinematic close-up is intentionally retained, not reinterpreted
 // as a world-space attack trajectory. All ordinary flight uses the shared world.
 const background=options.state==='ZOOM'?null:renderWorldView(snapshot,{sensor:options.sensor,palette:options.palette});
 return renderHUD({...options,world:background?{frame:background,pose:snapshot.pose}:null});
}
