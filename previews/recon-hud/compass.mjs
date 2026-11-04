import {variants} from './variants.mjs';

export const normalizeHeading=degrees=>((degrees%360)+360)%360;

// Synthetic heading integrates the signed bank cue; this is display motion,
// not an aircraft dynamics model. Rewinding visual time rewinds heading too.
export function simulatedHeading(time,index=0,variant=0){
 const profile=variants[variant]||variants[0],rate=.32*profile.rate;
 const turn=profile.bank*time+profile.sway*(1-Math.cos(time*rate))/rate;
 return normalizeHeading(82+index*13+turn*50);
}

export function northArrow(heading){
 const directions=[[0,-1],[-1,-1],[-1,0],[-1,1],[0,1],[1,1],[1,0],[1,-1]];
 const [dx,dy]=directions[Math.round(normalizeHeading(heading)/45)%8];
 const cardinal=dx===0||dy===0;
 return {tip:[dx*2,dy*2],tail:[-dx*2,-dy*2],left:cardinal?[-dy*2,dx*2]:[dx-dy,dy+dx],right:cardinal?[dy*2,-dx*2]:[dx+dy,dy-dx]};
}
