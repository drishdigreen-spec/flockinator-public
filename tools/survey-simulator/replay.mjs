import {readFile} from 'node:fs/promises';import {verifyReplay} from './session.mjs';
const args=process.argv.slice(2);if(args.length!==3||args[0]!=='--input'||args[2]!=='--verify')throw Error('Usage: node replay.mjs --input run.json --verify');
const data=await readFile(args[1]);if(data.length>16*1024*1024)throw Error('Replay too large');verifyReplay(JSON.parse(data));console.log('Replay verified');
