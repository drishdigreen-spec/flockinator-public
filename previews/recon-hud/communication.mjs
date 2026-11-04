import {stateAt} from './renderer.mjs';

// One event owns both endpoints. These are scripted messages, not radio telemetry.
export function communicationFrame(time,{scene='sequence',sceneStarted=0}={}){
 const result=Array(16).fill(null),elapsed=Math.max(0,time-sceneStarted);
 if(scene!=='sequence'&&!['SHARE','ALERT','ASSIGN','FRIEND'].includes(scene))return result;
 const slot=Math.floor(elapsed/2),start=sceneStarted+slot*2,age=time-start;
 if(age<0||age>=.625)return result;
 const available=i=>!['CRASH','EMPTY','NOLINK','ZOOM'].includes(stateAt(start,i));
 let sender=slot%16;
 if(scene==='sequence'){
  sender=Array.from({length:16},(_,i)=>(slot+i)%16).find(i=>['SHARE','ALERT','ASSIGN','FRIEND'].includes(stateAt(start,i)));
  if(sender===undefined)return result;
 }
 const senderState=scene==='sequence'?stateAt(start,sender):scene;
 if(['ALERT','ASSIGN','FRIEND'].includes(senderState)){
  result[sender]={direction:'TX',age,peer:'ALL'};
  for(let i=0;i<16;i++)if(i!==sender&&(scene!=='sequence'||available(i)))result[i]={direction:'RX',age,peer:sender};
  return result;
 }
 const receiver=Array.from({length:16},(_,i)=>(sender+5+i)%16).find(i=>i!==sender&&(scene==='SHARE'||available(i)));
 if(receiver===undefined)return result;
 result[sender]={direction:'TX',age,peer:receiver};
 result[receiver]={direction:'RX',age,peer:sender};
 return result;
}
