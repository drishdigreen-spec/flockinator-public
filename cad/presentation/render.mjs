import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
const require=createRequire('$HOME');
const {chromium}=require('playwright');
const browser=await chromium.launch({headless:true,channel:'chrome',args:['--enable-webgl','--ignore-gpu-blocklist']});
const page=await browser.newPage({viewport:{width:1600,height:1200},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text());});
await page.goto('http://127.0.0.1:8765/?render=1');await page.waitForFunction(()=>window.presentation?.ready,{timeout:30000});
const root=new URL('.',import.meta.url).pathname;
const shots=[['01-daylight','hero','day','white'],['02-dim-exhibition','hero','dim','white'],['03-warm-room','side','warm','white'],['04-front-unlit','front','off','white'],['05-charcoal-detail','detail','day','black'],['06-handheld-remote','remote','day','white'],['07-rear-service','rear','day','white'],['08-rounded-corner','corner','day','white']];
for(const [name,view,light,trim] of shots){await page.evaluate(({view,light,trim})=>{presentation.setView(view);presentation.setLighting(light);presentation.setTrim(trim);}, {view,light,trim});await page.waitForTimeout(1000);await page.screenshot({path:root+'renders/'+name+'.png'});console.log('RENDER',name);}
await page.evaluate(()=>{presentation.setView('hero');presentation.setLighting('day');presentation.setTrim('white');});
const download=page.waitForEvent('download');await page.evaluate(()=>document.getElementById('download').click());const d=await download;await d.saveAs(root+'Flockinator-concept.glb');
const info=await page.evaluate(()=>({rendered_triangles:presentation.renderer.info.render.triangles,webgl:presentation.renderer.capabilities.isWebGL2,parts:presentation.config.parts.length}));
await fs.writeFile(root+'render-validation.json',JSON.stringify({errors,...info,renders:shots.map(s=>s[0]),note:'Visual inspection required; lighting not calibrated'},null,2));console.log(JSON.stringify({errors,...info}));await browser.close();
