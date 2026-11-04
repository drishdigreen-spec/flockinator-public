// A presentation fixture: roles and P1/P2 labels are scripted, not inferred.
export const coordinationDuration=12;
export function coordinationFrame(time,start=0,participants=Array.from({length:16},(_,i)=>i)){
 const elapsed=Math.max(0,time-start),cycle=Math.floor(elapsed/coordinationDuration),phase=elapsed%coordinationDuration;
 const slot=(cycle*3)%participants.length,source=participants[slot],owner=participants[(slot+5)%participants.length],challenger=participants[(slot+9)%participants.length];
 const stage=phase<2?'ALERT':phase<4?'PRIORITY':phase<6?'CLAIM':phase<10?'ASSIGN':'OBSERVE';
 const nodes=Array.from({length:16},(_,index)=>({
  state:stage==='CLAIM'?(index===owner||index===challenger?'CLAIM':'CHECK'):stage==='ASSIGN'?(index===owner?'ASSIGN':'YIELD'):stage==='OBSERVE'?(index===owner?'SEEN':'SCAN'):stage,
  phase,owner,source,challenger,beacon:'P1',cycle
 }));
 const communications=Array(16).fill(null);
 const pair=(sender,receiver,age)=>{if(age>=0&&age<.625){communications[sender]={direction:'TX',peer:receiver,age};communications[receiver]={direction:'RX',peer:sender,age};}};
 const broadcast=age=>{if(age>=0&&age<.625)for(let i=0;i<16;i++)communications[i]={direction:i===source?'TX':'RX',peer:i===source?'ALL':source,age};};
 if(stage==='ALERT')broadcast(phase);
 if(stage==='CLAIM'){pair(owner,source,phase-4);pair(challenger,source,phase-4.875);}
 if(stage==='ASSIGN')broadcast(phase-6);
 return {stage,nodes,communications,cycle};
}
