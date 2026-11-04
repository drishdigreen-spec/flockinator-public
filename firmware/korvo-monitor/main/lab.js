const $=id=>document.getElementById(id), txt=(tag,text)=>Object.assign(document.createElement(tag),{textContent:text});
const links=['Clear','Muted','Half lost','Scrambled'], sectors=['Reed','Fern','Moss'];
const name=i=>String.fromCharCode(65+i%4)+(1+Math.floor(i/4));
let state,roundData,selected=0,frameKey='',pending=false,live=false,viewGeneration=0;
function disable(){ $('start').disabled=pending||!live;$('pause').disabled=pending||!live||state?.turn>=80; }
function displayRound(){
  const units=roundData?.units||[];
  $('units').replaceChildren(...units.map((u,i)=>{const b=txt('button','');b.append(txt('b',name(i)),txt('small',sectors[u.clear[0]]+' → '+sectors[u.altered[0]]));b.setAttribute('aria-pressed',i===selected);b.className=u.clear[0]===u.altered[0]?'':'changed';b.onclick=()=>{selected=i;displayRound();$('units').children[i]?.focus();};return b;}));
  const u=units[selected];$('inbox').replaceChildren();
  $('trace').textContent=u?name(selected)+' saw '+sectors[u.cue]+'. The true sector was '+sectors[u.truth]+'.':'Waiting for the first test round.';
  if(!u)return;
  [u.clear,u.altered].forEach((c,arm)=>{const box=txt('div','');box.append(txt('b',arm?links[state.link]:'Clear'));
    for(let j=0;j<3;j++){const peer=Math.floor(selected/4)*4+j+(j>=selected%4?1:0);
      box.append(txt('p',name(peer)+' · '+(c[1+j*2]===3?'No packet':'symbol '+c[1+j*2]+' → '+(sectors[c[2+j*2]]||'unknown'))));}
    box.append(txt('strong','Choice · '+sectors[c[0]]));$('inbox').append(box);});
}
async function replay(){
  const id=++viewGeneration,round=Number($('round').value);
  $('roundLabel').textContent=round+' / '+Math.max(0,state.turn-48);
  const key=state.run+'/'+round;
  if(state.turn<=48){frameKey='';roundData=null;displayRound();return;}
  if(key===frameKey)return;
  const r=await fetch('/api/round?run='+state.run+'&round='+round);if(!r.ok)return;
  const data=await r.json();if(id!==viewGeneration)return;roundData=data;frameKey=key;displayRound();
}
function render(s){
  if(!state||state.run!==s.run){$('seed').value=s.seed;$('link').value=s.link;frameKey='';roundData=null;$('follow').checked=true;}
  state=s;live=true;disable();
  const test=Math.max(0,s.turn-48);
  $('phase').textContent=(s.turn>=80?'Complete':s.paused?'Paused':s.turn<48?'Training':'Testing')+' · seed '+s.seed+' · '+(test?test+' / 32 test rounds':s.turn+' / 48 training rounds');
  $('pause').textContent=s.paused?'Resume':'Pause';
  for(const [id,i] of [['clear',0],['impaired',1],['solo',4]])$(id).textContent=s.scores[i][0]+' / '+test*4;
  $('rows').replaceChildren(...s.scores.slice(0,4).map((v,i)=>{const tr=txt('tr','');for(const x of [i<2?'Clear':links[s.link],i%2?links[s.link]:'Clear',v[1]+' / '+test*16,v[2],v[0]+' / '+test*4])tr.append(txt('td',x));return tr;}));
  $('memory').textContent=s.turn<48?'Training packets received: '+s.training_packets.join(' / '):'Correct sender–symbol meanings out of 144: clear training '+s.accurate[0]+', '+links[s.link].toLowerCase()+' training '+s.accurate[1]+'.';
  $('round').disabled=!test;$('round').max=Math.max(1,test);if($('follow').checked)$('round').value=Math.max(1,test);return replay();
}
async function poll(){try{const r=await fetch('/api/state');if(!r.ok)throw Error();const s=await r.json();if(!pending)await render(s);}catch{live=false;disable();$('phase').textContent='Controller disconnected · last view frozen';}finally{setTimeout(poll,550);}}
async function command(op){
  if(pending||!state||!live)return;pending=true;disable();
  try{const r=await fetch('/api/control',{method:'POST',headers:{'Content-Type':'application/x-flock-lab'},body:[op,state.revision,$('seed').value,$('link').value].join(' ')});
    if(!r.ok)throw Error('Command declined ('+r.status+'). Review the current run before retrying.');await render(await r.json());$('error').textContent='';
  }catch(e){$('error').textContent=e.message;}finally{pending=false;disable();}
}
$('controls').onsubmit=e=>{e.preventDefault();command('start');};$('pause').onclick=()=>command(state.paused?'resume':'pause');
$('round').oninput=()=>{$('follow').checked=false;replay().catch(()=>{});};poll();
