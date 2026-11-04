const $ = id => document.getElementById(id);
const board = $('board'), ctx = board.getContext('2d');
const S=48, left=37, top=27;
const names=Array.from({length:16},(_,i)=>String.fromCharCode(65+i%4)+(1+Math.floor(i/4)));
let data=null, pending=false, connected=false, cursor=[7,3];
const tile=([x,y])=>String.fromCharCode(65+x)+(y+1);
const center=([x,y])=>[left+S*(x+.5),top+S*(y+.5)];
function draw(){
  if(!data)return;
  const {plan:p,sim}=data, seen=new Set(sim.seen.map(String));
  ctx.fillStyle='#101e19';ctx.fillRect(0,0,board.width,board.height);
  ctx.textAlign='center';ctx.font='14px monospace';ctx.fillStyle='#b3c6bb';
  for(let x=0;x<16;x++)ctx.fillText(String.fromCharCode(65+x),center([x,0])[0],18);
  for(let y=0;y<12;y++)ctx.fillText(y+1,19,center([0,y])[1]+5);
  for(let y=0;y<12;y++)for(let x=0;x<16;x++){
    const a=left+x*S,b=top+y*S;
    ctx.fillStyle=seen.has(String([x,y]))?'#30584b':'#1b3028';ctx.fillRect(a+1,b+1,S-2,S-2);
    if(Math.abs(y-p.focus[1])<=1){ctx.strokeStyle='#658265';ctx.beginPath();for(let j=1;j<=3;j++){ctx.moveTo(a+3,b+j*11);ctx.lineTo(a+j*11,b+3);}ctx.stroke();}
  }
  const selected=Number($('unit').value);
  sim.paths.forEach((path,i)=>{
    const points=[[7,11]];
    for(const end of path){
      let [x,y]=points.at(-1);
      while(x!==end[0]||y!==end[1]){x+=Math.sign(end[0]-x);y+=Math.sign(end[1]-y);points.push([x,y]);}
    }
    ctx.strokeStyle=i===selected?'#ffdc85':'#9dccb566';ctx.lineWidth=i===selected?2.4:1.4;
    ctx.beginPath();points.forEach((pt,k)=>{const [a,b]=center(pt);if(k)ctx.lineTo(a,b);else ctx.moveTo(a,b);});ctx.stroke();
    if(i===selected)for(const pt of path){const [a,b]=center(pt);ctx.fillStyle='#ffdc85';ctx.fillRect(a-3,b-3,6,6);}
  });
  ctx.lineWidth=1;ctx.font='bold 24px monospace';
  for(const [pt,symbol,color] of [[[7,11],'△','#e6f6df'],[p.focus,'◎','#ebcf80']]){const [a,b]=center(pt);ctx.fillStyle=color;ctx.fillText(symbol,a,b+8);}
  p.contacts.forEach((c,i)=>{
    const reports=sim.reports[i],labels=new Set(reports.map(r=>r.label));
    const kind=$('truth').checked?c.kind:labels.size===1?reports[0].label:null;
    if(!$('truth').checked&&!reports.length)return;
    const [a,b]=center(c.pos);ctx.fillStyle=kind==='Enemy'?'#ffab90':kind==='Friendly'?'#9bdaf0':'#e5d19b';
    ctx.fillText('◇',a,b+7);ctx.font='bold 12px monospace';ctx.fillText(String(i+1),a,b+4);ctx.font='bold 24px monospace';
  });
  if(data.phase!=='Draft'){
    const groups=new Map();
    sim.units.forEach((u,i)=>{const key=String(u.pos);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(i);});
    ctx.font='bold 13px monospace';for(const ids of groups.values()){const [a,b]=center(sim.units[ids[0]].pos);const label=ids.length===1?names[ids[0]]:ids.length+' units';ctx.fillStyle='#10271f';ctx.fillRect(a-24,b+8,48,16);ctx.fillStyle='#cfffd7';ctx.fillText(label,a,b+21);}
  }
  if(document.activeElement===board){ctx.strokeStyle='#ffffff';ctx.lineWidth=2;ctx.strokeRect(left+cursor[0]*S+2,top+cursor[1]*S+2,S-4,S-4);}
}
function el(tag,text){const e=document.createElement(tag);e.textContent=text;return e;}
function showReports(){
  const {plan:p,sim}=data,reveal=$('truth').checked;
  const cards=p.contacts.map((c,i)=>{
    const reports=sim.reports[i],labels=new Set(reports.map(r=>r.label));
    if(!reveal&&!reports.length)return null;
    const box=el('div','');box.className='report';const info=el('div','');
    const verdict=!reports.length?'No sighting':labels.size>1?'Conflicting reports':reports.length>1?'Corroborated '+reports[0].label:'Unconfirmed '+reports[0].label;
    info.append(el('strong','#'+(i+1)+' · '+tile(c.pos)+' · '+verdict),el('p',c.priority+' priority'+(reveal?' · Placed as '+c.kind+(data.beyond_return.includes(i)?' · Beyond return range':''):'')),
      el('small',reports.map(r=>names[r.unit]+' '+r.label+' (turn '+r.turn+')').join(' / ')));
    const check=sim.checks.find(v=>v.contact===i);
    if(check)info.append(el('p','Independent check assigned to '+names[check.unit]+' on turn '+check.turn+'.'));
    const select=document.createElement('select');select.setAttribute('aria-label','Director outcome for contact '+(i+1));
    for(const word of ['Unassessed','Intact','Damaged','Removed'])select.add(new Option(word,word));
    select.value=c.outcome;select.disabled=!connected||pending;
    select.onchange=()=>submit({op:'assess',index:i,outcome:select.value});
    const label=el('label','Director outcome');label.append(select);box.append(info,label);return box;
  }).filter(Boolean);
  // Keep an open native outcome menu intact while the clock advances.
  if(!$('contacts').contains(document.activeElement))$('contacts').replaceChildren(...cards);
  $('report-summary').textContent=!p.contacts.length?'Place a friendly or enemy contact on the board.':
    reveal?sim.reports.filter(r=>r.length).length+' of '+p.contacts.length+' contacts sighted. Corroboration requires two independent units to agree.':cards.length+' reported contacts. Planner truth is hidden.';
}
function controls(){
  const offline=!data||!connected||pending,draft=data?.phase==='Draft';
  $('randomize').disabled=$('scenario-seed').disabled=offline||(!draft&&data?.phase!=='Complete');
  $('tools').disabled=$('config').disabled=$('reroll').disabled=offline||!draft;
  $('play').disabled=offline||!['Paused','Draft'].includes(data?.phase);
  $('pause').disabled=offline||data?.phase!=='Running';$('edit').disabled=offline||draft;
}
function render(){
  const {plan:p,sim,phase}=data;
  $('phase').textContent=phase+' · Turn '+sim.turn;$('coverage').textContent=sim.seen.length+' / 192 tiles seen';
  for(const key of ['pattern','count','cover','battery'])$(key).value=String(p[key]);
  if($('unit').options.length!==p.count){const old=Number($('unit').value);$('unit').replaceChildren(...names.slice(0,p.count).map((s,i)=>new Option(s,i)));$('unit').value=Math.min(old,p.count-1);}
  const fit=sim.units.filter(u=>u.planned+3<=p.battery).length;
  $('budget').textContent=fit+' of '+p.count+' routes fit the pack with a three-point landing reserve. Longer routes turn back early.';
  $('odds').textContent='In the tree line: '+data.odds[0]+'% chance of sighting, then '+data.odds[1]+'% chance of a correct label. Open tiles use 85% and 82%.';
  if(phase==='Complete'&&$('truth').checked){
    const claims=sim.reports.map((rs,i)=>({rs,truth:p.contacts[i].kind})).filter(({rs})=>rs.length>=2&&rs.every(r=>r.label===rs[0].label));
    $('debrief').textContent=claims.length+' corroborated contacts · '+claims.filter(({rs,truth})=>rs[0].label===truth).length+' correct against planner truth.';
  }else $('debrief').textContent='';
  const outside=$('truth').checked?' · '+data.beyond_return.length+' contacts beyond round-trip range':'';
  $('scenario-info').textContent=(p.scenario_seed==null?'Custom board':'Scenario seed '+p.scenario_seed)+outside;
  $('seed').textContent='Draw '+p.seed+'. Replaying the same plan and draw reproduces the reports.';
  $('play').textContent=phase==='Paused'?'Resume rehearsal':'Run rehearsal';
  $('units').replaceChildren(...sim.units.map((u,i)=>{const e=el('div','');e.className='unitcard';e.append(el('strong',names[i]+' · '+(phase==='Draft'?'Planned':u.role)),el('small',tile(u.pos)+' · '+u.energy+' pts · '+(p.custom[i]?'Custom route':'Preset route')),el('small',u.reason||('Round trip '+u.planned+' steps')));return e;}));
  controls();showReports();draw();
}
let generation=0;
async function submit(action){
  if(!connected||!data||pending)return;
  pending=true;generation++;controls();
  try{const r=await fetch('/api/planner',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...action,revision:data.plan.revision})});const result=await r.json();if(!r.ok)throw Error(result.error);data=result;$('error').textContent='';}
  catch(e){$('error').textContent=e.message;}
  finally{pending=false;render();}
}
async function poll(){
  const version=generation;
  try{if(!pending){const r=await fetch('/api/planner');if(!r.ok)throw Error();const next=await r.json();if(!pending&&version===generation){data=next;connected=true;render();}}}
  catch{connected=false;controls();$('phase').textContent='Host disconnected';}
  setTimeout(poll,900);
}
function setCursor(pt){cursor=pt;$('col').value=pt[0]+1;$('row').value=pt[1]+1;draw();}
function applyTile(pos){
  if(!data||data.phase!=='Draft')return;
  const tool=$('tool').value;
  if(tool==='Friendly'||tool==='Enemy')submit({op:'contact',pos,kind:tool,priority:$('priority').value});
  else if(tool==='waypoint')submit({op:tool,pos,unit:Number($('unit').value)});
  else submit({op:tool,pos});
}
function pointer(e){const r=board.getBoundingClientRect();return [Math.floor(((e.clientX-r.left)*board.width/r.width-left)/S),Math.floor(((e.clientY-r.top)*board.height/r.height-top)/S)];}
const inside=([x,y])=>Number.isInteger(x)&&Number.isInteger(y)&&x>=0&&x<16&&y>=0&&y<12;
board.onclick=e=>{const pt=pointer(e);if(inside(pt)){setCursor(pt);applyTile(pt);}};
board.onkeydown=e=>{const d={ArrowUp:[0,-1],ArrowDown:[0,1],ArrowLeft:[-1,0],ArrowRight:[1,0]}[e.key];if(d){e.preventDefault();const pt=cursor.map((v,i)=>v+d[i]);if(inside(pt))setCursor(pt);}else if(['Enter',' '].includes(e.key)){e.preventDefault();applyTile(cursor);}};
board.onfocus=board.onblur=draw;
$('place').onclick=()=>{const pt=[Number($('col').value)-1,Number($('row').value)-1];if(inside(pt)){setCursor(pt);applyTile(pt);}else $('error').textContent='Choose a column from 1–16 and a row from 1–12.';};
for(const key of ['pattern','count','cover','battery'])$(key).onchange=e=>submit({op:'setting',key,value:['count','battery'].includes(key)?Number(e.target.value):e.target.value});
for(const op of ['play','pause','reroll'])$(op).onclick=()=>submit({op});
$('edit').onclick=()=>{if(confirm('Return to planning and clear rehearsal progress? Your routes and contacts are kept.'))submit({op:'edit'});};
for(const op of ['undo','preset'])$(op).onclick=()=>submit({op,unit:Number($('unit').value)});
$('unit').onchange=draw;$('truth').onchange=()=>{if(data)render();};poll();

$('randomize').onclick=()=>{
  const raw=$('scenario-seed').value,seed=raw===''?null:Number(raw);
  if(!$('scenario-seed').checkValidity()||(seed!==null&&!Number.isInteger(seed))){
    $('error').textContent='Enter a whole-number seed from 0 to 4294967295.';return;
  }
  if(confirm('Generate a new board and replace the current routes and contacts? Saved exercise journals are kept.'))submit({op:'randomize',seed});
};
let history=[];
function journalLink(){
  const run=$('episodes').value,entry=history.find(x=>x.run===run);
  $('download').hidden=!entry;
  if(entry){
    $('download').href='/api/planner/journals/'+run+'.zip';
    $('download').download='flock-'+run+'.zip';
    $('card-status').textContent=entry.finalized?'SD copies verified for '+(entry.verified.join(', ')||'no panels yet')+'.':'Host snapshot available. SD delivery starts when the rehearsal closes.';
  }else $('card-status').textContent='Start a new rehearsal to record its unit memories.';
}
$('episodes').onchange=journalLink;
async function refreshHistory(){
  try{
    const r=await fetch('/api/planner/journals');if(!r.ok)throw Error();
    const next=await r.json();
    if(JSON.stringify(next)!==JSON.stringify(history)||!next.length){
      const previous=$('episodes').value;history=next;
      $('episodes').replaceChildren(...next.map(x=>new Option(new Date(Number(x.run.slice(0,13))).toLocaleString()+' · '+x.run.slice(-4),x.run)));
      if(next.some(x=>x.run===previous))$('episodes').value=previous;
      journalLink();
    }
  }catch{$('card-status').textContent='Exercise history unavailable.';}
  setTimeout(refreshHistory,3000);
}
refreshHistory();
