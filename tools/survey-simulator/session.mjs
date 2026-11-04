import {createState,command,advance,VERSION,scenario} from './engine.mjs';
import {isDeepStrictEqual} from 'node:util';
export class Session {
 constructor(run){this.state=createState(run);this.initialRun=run;this.log=[];this.clients=new Map();this.nextClient=1;this.steps=0;}
 register(token=null){
  if(token!==null&&(typeof token!=='string'||!/^[-a-zA-Z0-9_]{16,80}$/.test(token)))throw Error('Invalid client token');
  if(token!==null)for(const [id,client] of this.clients)if(client.token===token){this.clients.delete(id);this.clients.set(id,client);return id;}
  // IDs are never reused: evicted envelopes cannot affect a new client's state.
  if(!Number.isSafeInteger(this.nextClient))throw Error('Client ID limit reached');
  if(this.clients.size>=32)this.clients.delete(this.clients.keys().next().value);
  const id=this.nextClient++;this.clients.set(id,{token,high:0,results:new Map()});return id;
 }
 submit(c){
  if(!c||Object.keys(c).sort().join(',')!=='client,command,run,seq'||c.run!==this.state.run||!Number.isSafeInteger(c.seq)||c.seq<1)throw Error('Invalid session or envelope');
  const client=this.clients.get(c.client);if(!client)throw Error('Unknown client');
  this.clients.delete(c.client);this.clients.set(c.client,client);
  const key=JSON.stringify(c.command),cached=client.results.get(c.seq);
  if(cached){if(cached.key!==key)throw Error('Conflicting command ID');return cached.result;}
  if(c.seq<=client.high)throw Error('Stale command sequence');
  if(c.command?.op==='reset'){
   if(Object.keys(c.command).length!==1||this.state.run===0xffffffff)throw Error('Invalid reset');
   this.state=createState(this.state.run+1);this.initialRun=this.state.run;this.log=[];this.steps=0;
  }else{
   if(this.log.length>=20000)throw Error('Export and reset: command limit');
   this.state=command(this.state,c.command);this.log.push({step:this.steps,command:structuredClone(c.command)});
  }
  const result={ok:true,run:this.state.run,tick:this.state.tick};client.high=c.seq;client.results.set(c.seq,{key,result});
  if(client.results.size>128)client.results.delete(client.results.keys().next().value);
  return result;
 }
 step(ticks){this.state=advance(this.state,ticks);this.steps+=ticks;}
 export(){return {version:VERSION,scenarioVersion:scenario.version,initialRun:this.initialRun,steps:this.steps,commands:structuredClone(this.log),state:structuredClone(this.state)};}
}
export function verifyReplay(data){
 if(data?.version!==VERSION||data.scenarioVersion!==scenario.version||!Number.isSafeInteger(data.steps)||data.steps<0||data.steps>10000000||!Array.isArray(data.commands)||data.commands.length>20000)throw Error('Incompatible or oversized replay');
 let s=createState(data.initialRun),step=0;
 const advanceTo=end=>{if(!Number.isSafeInteger(end)||end<step||end>data.steps)throw Error('Invalid replay order');while(step<end){const n=Math.min(10000,end-step);s=advance(s,n);step+=n;}};
 for(const entry of data.commands){advanceTo(entry.step);s=command(s,entry.command);}
 advanceTo(data.steps);if(!isDeepStrictEqual(s,data.state))throw Error('Replay mismatch');return true;
}
