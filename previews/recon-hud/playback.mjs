export const reversibleStates=new Set(['HOLD','SCAN','SEEN','SHARE','CHECK','DOUBT','ENGAGE','LOST','ALERT','PRIORITY','CLAIM','ASSIGN','YIELD']);

// Reflect elapsed time before easing, so mirrored samples are exactly equal.
// The four-second passage slows to a stop at either end of its eight-second cycle.
export function pingPong(elapsed){
 const cycle=((elapsed%8)+8)%8,passage=cycle<=4?cycle:8-cycle;
 return 2*(1-Math.cos(Math.PI*passage/4));
}
export const visualPhase=(state,elapsed)=>reversibleStates.has(state)?pingPong(elapsed):elapsed;
