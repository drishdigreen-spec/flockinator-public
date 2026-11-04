import {drawMap,validMapSnapshot,installFullscreen,observeMapSize} from './mission-map.mjs';
const canvas=document.getElementById('mission-map'),status=document.getElementById('map-status');
installFullscreen(document.getElementById('mission-map-section'),document.getElementById('map-fullscreen'),status);
const session=new URLSearchParams(location.search).get('session');
let lastReceived=0,seen=false,latestMap=null;
observeMapSize(canvas,()=>latestMap);
if(!session||! /^[a-f0-9-]{36}$/.test(session)||typeof BroadcastChannel!=='function'){
 status.textContent='Open this map from “Open map tab” in the camera preview.';
 status.dataset.state='stale';
}else{
 const channel=new BroadcastChannel('flock-map-'+session);
 channel.onmessage=event=>{
  if(event.data?.kind==='map-inactive'){
   seen=true;lastReceived=performance.now();status.textContent='Select Mission loop in the camera preview to resume.';status.dataset.state='inactive';return;
  }
  if(!validMapSnapshot(event.data))return;
  const s=event.data;seen=true;lastReceived=performance.now();latestMap=s;drawMap(canvas,s);
  status.dataset.state='live';status.textContent='Linked preview · Mission '+(s.cycle+1)+' · '+s.stage+' · '+Math.floor(s.elapsed)+'s'+(s.playing?'':' · Paused');
 };
 function request(){
  channel.postMessage({kind:'request-map'});
  if(performance.now()-lastReceived>2000){status.dataset.state='stale';status.textContent=seen?'Preview disconnected · last view held':'Waiting for the originating camera preview…';}
 }
 request();setInterval(request,125);
}
