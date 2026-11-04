const $=id=>document.getElementById(id);
const el=(tag,text)=>Object.assign(document.createElement(tag),{textContent:text});
const fraction=(n,total)=>n+' / '+total;
function row(values){const tr=document.createElement('tr');for(const v of values)tr.append(el('td',v));return tr;}
let result, selected=0, timer=null;
function stop(){clearInterval(timer);timer=null;$('watch').textContent='Play rounds';}
function trace(){
  const round=Number($('round').value);
  $('round-text').textContent=round+' / '+result.learning.test_rounds;
  const cells=result.learning.replay.slice((round-1)*16,round*16);
  if(!$('agents').children.length)for(let i=0;i<16;i++){
    const button=el('button','');button.onclick=()=>{selected=i;trace();};$('agents').append(button);
  }
  cells.forEach((x,i)=>{
    const b=$('agents').children[i];
    b.setAttribute('aria-pressed',String(i===selected));
    b.className=x.clear.choice!==x.impaired.choice?'changed':'';
    b.replaceChildren(el('b',x.clear.unit),el('small',x.clear.choice+' → '+x.impaired.choice));
  });
  const pair=cells[selected];
  $('cue').textContent=pair.clear.unit+' saw '+pair.clear.cue+' in round '+pair.clear.round+'. The debrief revealed '+pair.clear.truth+'. Both replays use the same trained listener.';
  $('pair').replaceChildren(...[pair.clear,pair.impaired].map((d,i)=>{
    const card=document.createElement('article');card.append(el('h3',i?result.link:'Clear'));
    for(const m of d.messages)card.append(el('p',m.sender+' · symbol '+m.token+' → '+(m.decoded||'unknown')));
    if(!d.messages.length)card.append(el('p','No peer packet arrived.'));
    card.append(el('strong','Choice · '+d.choice));return card;
  }));
}
function render(){
  const l=result.learning,[clear,blocked,transfer]=l.rows;
  $('headline').replaceChildren(...[clear,blocked].map(r=>{
    const d=el('div','');d.append(el('span',r.test+' during test'),el('b',fraction(r.recoveries,r.tasks)),el('span','team recoveries after clear training'));return d;
  }));
  $('scores').replaceChildren(...l.rows.map(r=>row([r.train,r.test,r.packets,fraction(r.correct,r.decisions),fraction(r.recoveries,r.tasks)])));
  $('solo').textContent='Private clues alone recovered '+fraction(l.solo.recoveries,l.solo.tasks)+' samples. Each score includes all four teams across all 32 held-out rounds.';
  $('memory').textContent='After clear training, listeners correctly decoded '+clear.accurate+' of 144 sender–symbol meanings. Training with '+result.link.toLowerCase()+' signals yielded '+transfer.accurate+' correct meanings. Listeners had enough evidence to interpret '+clear.known+' and '+transfer.known+' meanings respectively.';
  $('transfer').textContent='With a clear link restored at test time, the two sets of memories recovered '+clear.recoveries+' and '+transfer.recoveries+' samples out of '+clear.tasks+'.';
  selected=l.first_change%16;$('round').value=1+Math.floor(l.first_change/16);
  $('changed').textContent='Changing the test channel changed '+l.changed_choices+' of '+clear.decisions+' individual choices. The replay opens on the first changed choice when one exists.';
  trace();
  const m=result.mission;
  $('mission').textContent=result.board+' board · draw '+m.seed+' · '+m.count+' units · '+m.contacts+' contacts.';
  const metrics={sent:'Requests sent',delivered:'Requests delivered',correct:'Correctly corroborated contacts',incorrect:'Incorrectly corroborated contacts',seen:'Tiles seen',spent:'Energy spent',home:'Units home'};
  $('metrics').replaceChildren(...Object.entries(metrics).map(([k,title])=>row([title,m.clear[k],m.muted[k]])));
  const first=m.messages[0][0];
  $('request').textContent=first?'First clear-link request: '+first.sender+' asked '+first.recipient+' to check contact '+first.contact+' on turn '+first.turn+'.':'No check request was sent on this board. Withholding requests had no opportunity to affect the mission.';
}
async function run(e){
  e?.preventDefault();stop();$('controls').querySelector('.primary').disabled=true;$('export').disabled=true;
  $('status').textContent='Running matched trials…';
  try{
    const r=await fetch('/api/lab',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({seed:Number($('seed').value),board:$('board').value,link:$('link').value})});
    const v=await r.json();if(!r.ok)throw Error(v.error);
    result=v;render();$('export').disabled=false;$('status').textContent='Results for seed '+v.seed+' · '+v.link+' intervention · '+v.version;
  }catch(err){$('status').textContent='Comparison failed. '+err.message;}
  finally{$('controls').querySelector('.primary').disabled=false;}
}
$('controls').onsubmit=run;
$('round').oninput=()=>{if(result){stop();trace();}};
$('watch').onclick=()=>{if(timer){stop();return;}if(!result)return;
  $('watch').textContent='Pause replay';
  timer=setInterval(()=>{$('round').value=Number($('round').value)%result.learning.test_rounds+1;trace();},1200);
};
$('export').onclick=()=>{const a=document.createElement('a'),url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));a.href=url;a.download='flock-lab-'+result.seed+'-'+result.link+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
run();
