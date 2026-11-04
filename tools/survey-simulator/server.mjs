import http from 'node:http';import {readFile} from 'node:fs/promises';import {fileURLToPath} from 'node:url';import {resolve,dirname} from 'node:path';import {homedir} from 'node:os';import {readFileSync,writeFileSync,mkdirSync,renameSync} from 'node:fs';
import {Session} from './session.mjs';import {snapshot,wireSnapshot,scenario} from './engine.mjs';
const preview=new URL('../../previews/recon-hud/',import.meta.url);
const assets=new Set(['survey.html','survey-app.mjs','survey.css','world-view.mjs','renderer.mjs','compass.mjs','survey-playback.mjs','readouts.mjs','variants.mjs','playback.mjs']);
export function createServer({run=Math.floor(Date.now()/1000),saveRun=()=>{}}={}){
 const session=new Session(run);let seq=0,last=performance.now(),lagMs=0;
 const timer=setInterval(()=>{const now=performance.now(),due=Math.floor((now-last)/100);if(due){session.step(Math.min(due,5));last+=due*100;if(due>5)lagMs+=(due-5)*100;}},100);timer.unref();
 const server=http.createServer(async(req,res)=>{
  const json=(status,value)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(JSON.stringify(value));};
  try{
   const port=server.address().port,hosts=[`127.0.0.1:${port}`,`localhost:${port}`];
   if(!hosts.includes(req.headers.host)||req.headers.origin&&!hosts.some(h=>req.headers.origin===`http://${h}`)||req.headers['sec-fetch-site']==='cross-site')return json(403,{error:'Local origin required'});
   const path=new URL(req.url,'http://127.0.0.1').pathname;
   if(req.method==='GET'&&path==='/favicon.ico'){res.writeHead(204);res.end();return;}
   if(req.method==='GET'&&path==='/api/state'){
    seq++;return json(200,{version:2,run:session.state.run,tick:session.state.tick,paused:session.state.paused,lagMs,limit:session.state.limit,sites:scenario.sites,nodes:session.state.nodes.map(n=>snapshot(session.state,n.id,seq)),wire:session.state.nodes.map(n=>wireSnapshot(session.state,n.id,seq)),events:session.state.events.slice(-32)});
   }
   if(req.method==='GET'&&path==='/api/replay')return json(200,session.export());
   if(req.method==='POST'&&['/api/clients','/api/commands'].includes(path)){
    if(req.headers['content-type']!=='application/json')return json(415,{error:'JSON required'});
    if(Number(req.headers['content-length'])>4096){req.resume();return json(413,{error:'Request too large'});}
    let body='',bytes=0;for await(const chunk of req){bytes+=chunk.length;if(bytes>4096){json(413,{error:'Request too large'});return;}body+=chunk;}
    const value=JSON.parse(body);if(path==='/api/clients'){
     if(!value||Array.isArray(value)||typeof value!=='object'||Object.keys(value).some(k=>k!=='token'))throw Error('Invalid client registration');
     const client=session.register(value.token??null);return json(200,{client,seq:session.clients.get(client).high});
    }
    const result=session.submit(value);if(value.command?.op==='reset')saveRun(session.state.run);return json(200,result);
   }
   const name=path==='/'?'survey.html':path.slice(1);
   if(req.method!=='GET'||!assets.has(name))return json(404,{error:'Not found'});
   const data=await readFile(new URL(name,preview));res.writeHead(200,{'Content-Type':name.endsWith('.mjs')?'text/javascript':name.endsWith('.css')?'text/css':'text/html','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'"});res.end(data);
  }catch(e){if(!res.headersSent)json(400,{error:e.message});else res.end();}
 });
 server.maxConnections=32;server.requestTimeout=5000;server.headersTimeout=5000;server.on('close',()=>clearInterval(timer));return server;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args=process.argv.slice(2);let port=8767;
 for(let i=0;i<args.length;i+=2){if(args[i]==='--host'&&args[i+1]==='127.0.0.1')continue;if(args[i]==='--port'&&/^\d+$/.test(args[i+1]))port=Number(args[i+1]);else throw Error('Usage: --host 127.0.0.1 --port 8767');}
 if(port<1024||port>65535)throw Error('Invalid port');
 const counterFile=resolve(homedir(),'.local/share/flockinator/survey-session.json');
 let previous=0;try{previous=JSON.parse(readFileSync(counterFile,'utf8')).run;if(!Number.isInteger(previous)||previous<0||previous>=0xffffffff)throw Error('Invalid persisted session');}catch(e){if(e.code!=='ENOENT')throw e;}
 const run=Math.max(previous+1,Math.floor(Date.now()/1000));
 const saveRun=value=>{mkdirSync(dirname(counterFile),{recursive:true});writeFileSync(counterFile+'.tmp',JSON.stringify({run:value}),{mode:0o600});renameSync(counterFile+'.tmp',counterFile);};saveRun(run);
 createServer({run,saveRun}).listen(port,'127.0.0.1',()=>console.log(`Fictional survey: http://127.0.0.1:${port}`));
}
