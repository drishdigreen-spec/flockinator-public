const $ = id => document.getElementById(id);
const ctx = document.querySelector('canvas').getContext('2d');
let current, sending = false;
function buttons() {
  $('start').disabled = $('stop').disabled = !current || sending || current.busy;
}
function render(data) {
  const m = data.mission;
  if (!current || current.mission.request !== m.request) {
    $('scenario').selectedIndex = m.scenario;
    $('goal').selectedIndex = m.goal;
    $('seconds').value = m.seconds;
    $('repeat').checked = m.repeat;
  }
  current = data;
  $('controller-lab').hidden = !data.controller_lab;
  if (data.controller_lab) $('controller-lab').href='http://'+data.controller_lab+'/';
  buttons();
  $('status').textContent = data.status + (m.run ? ' · Run ' + m.run : '');
  $('summary').textContent = 'Korvo ' + (data.prop ? 'connected' : 'disconnected') +
    (data.status === 'Running' ? ' · T+' + Math.floor(data.elapsed / 1000) + ' s' : '');
  const missing = m.result && data.nodes.filter(n => !m.result.includes(n.label));
  $('result').textContent = data.busy ? 'Sending to the fleet…' : m.result ?
    m.result.length + '/16 panels verified' + (missing.length ? ' · Unverified: '+missing.map(n=>n.label).join(', ') : '') :
    m.request ? 'Last dispatch result unknown.' : 'Ready for a mission.';
  ctx.fillStyle = '#102321'; ctx.fillRect(0,0,800,360);
  ctx.strokeStyle = '#24423c'; ctx.beginPath();
  for (let i=0;i<800;i+=40) { ctx.moveTo(i,0); ctx.lineTo(i,360); }
  for (let i=0;i<360;i+=40) { ctx.moveTo(0,i); ctx.lineTo(800,i); }
  ctx.stroke();
  const units = data.nodes.map(n => {
    if (data.status === 'Running') {
      const x=(n.pose[0]+90)*2.3, y=(220-n.pose[1])*1.1;
      ctx.fillStyle='#c3f1cf'; ctx.fillRect(x-2,y-2,5,5);
      ctx.font='13px monospace'; ctx.fillText(n.label,x+5,y);
    }
    const li=document.createElement('li'), detail=document.createElement('small');
    li.textContent=n.label+' · '+n.state;
    const health=n.health?.split(' ')[2];
    detail.textContent=({'0':'No response','1':'Panel online','2':'Panel error'})[health] || 'Awaiting telemetry';
    li.append(detail); return li;
  });
  $('fleet').replaceChildren(...units);
}
async function api(path, body) {
  const response = await fetch(path, body ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : {});
  const data = await response.json();
  if (!response.ok) throw Error(data.error);
  return data;
}
async function poll() {
  try { render(await api('/api/state')); }
  catch { current=null; buttons(); $('status').textContent='Host disconnected · last view frozen'; }
  setTimeout(poll, 750);
}
async function submit(start) {
  if (!current || sending || current.busy) return;
  sending=true; buttons(); $('error').textContent='';
  try {
    await api('/api/mission', {previous:current.mission.request,start,scenario:$('scenario').selectedIndex,
      goal:$('goal').selectedIndex,seconds:Number($('seconds').value),repeat:$('repeat').checked});
    render(await api('/api/state'));
  } catch (e) { $('error').textContent=e.message; }
  finally { sending=false; buttons(); }
}
$('start').onclick=()=>submit(true);
$('stop').onclick=()=>submit(false);
poll();
