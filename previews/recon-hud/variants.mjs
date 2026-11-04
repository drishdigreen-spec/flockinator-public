// The same ten flight treatments have state-specific observation/failure behaviour.
export const variants=[
 {name:'Steady glide',bank:0,sway:.12,pitch:-2,heave:2,rate:.8,speed:.8,offset:0,targetX:6,targetY:3,exit:0,roll:1,rollTime:1.5,zoomPower:2,zoomMax:4},
 {name:'Left bank',bank:-.3,sway:.14,pitch:0,heave:3,rate:.7,speed:1,offset:.8,targetX:10,targetY:4,exit:Math.PI,roll:-1,rollTime:1.2,zoomPower:1.4,zoomMax:3.5},
 {name:'Right bank',bank:.3,sway:.16,pitch:-3,heave:2.5,rate:.9,speed:1.1,offset:1.6,targetX:8,targetY:6,exit:.4,roll:1,rollTime:1.8,zoomPower:2.6,zoomMax:4.5},
 {name:'Climbing',bank:-.08,sway:.18,pitch:5,heave:3,rate:.6,speed:.7,offset:2.4,targetX:5,targetY:7,exit:-1.2,roll:-1,rollTime:1.9,zoomPower:1.7,zoomMax:4.2},
 {name:'Descending',bank:.06,sway:.16,pitch:-7,heave:2,rate:.8,speed:1.3,offset:3.2,targetX:9,targetY:3,exit:1.2,roll:1,rollTime:1.1,zoomPower:2.8,zoomMax:3.8},
 {name:'Weaving',bank:0,sway:.43,pitch:-1,heave:4,rate:1.6,speed:1,offset:4,targetX:11,targetY:5,exit:-2.1,roll:-1,rollTime:1.6,zoomPower:2.2,zoomMax:4.7},
 {name:'Gusty flight',bank:.12,sway:.3,pitch:1,heave:5,rate:2.2,speed:.9,offset:4.8,targetX:6,targetY:8,exit:2.1,roll:1,rollTime:1.35,zoomPower:1.2,zoomMax:3.7},
 {name:'Wide turn',bank:-.4,sway:.12,pitch:-4,heave:2,rate:.45,speed:.6,offset:5.6,targetX:12,targetY:4,exit:Math.PI+.3,roll:-1,rollTime:2.1,zoomPower:3,zoomMax:4.3},
 {name:'Low approach',bank:.1,sway:.1,pitch:-9,heave:1.5,rate:1.1,speed:1.6,offset:6.4,targetX:4,targetY:6,exit:-.5,roll:1,rollTime:1.65,zoomPower:1.8,zoomMax:4.8},
 {name:'Survey sweep',bank:.25,sway:.3,pitch:3,heave:3.5,rate:1.25,speed:1.2,offset:7.2,targetX:10,targetY:7,exit:2.7,roll:-1,rollTime:1.4,zoomPower:2.4,zoomMax:3.6}
];
function mix(n){n=Math.imul(n^(n>>>16),0x45d9f3b);n=Math.imul(n^(n>>>16),0x45d9f3b);return (n^(n>>>16))>>>0;}
function shuffled(seed){
 const bag=Array.from({length:10},(_,i)=>i);let value=seed;
 for(let i=9;i>0;i--){value=mix(value+0x9e3779b9);const j=value%(i+1);[bag[i],bag[j]]=[bag[j],bag[i]];}
 return bag;
}
export function chooseVariant({seed=0,index=0,state='HOLD',occurrence=0}={}){
 const visit=Math.max(0,Math.floor(occurrence)),block=Math.floor(visit/10);
 let key=mix(seed^Math.imul(index+1,0x27d4eb2d));
 for(const character of state)key=mix(key^character.charCodeAt(0));
 const bagFor=b=>shuffled(mix(key^Math.imul(b+1,0x85ebca6b)));
 const bag=bagFor(block);
 // Swapping the first two never changes the previous set's last entry.
 if(block>0&&bag[0]===bagFor(block-1)[9])[bag[0],bag[1]]=[bag[1],bag[0]];
 return bag[visit%10];
}
