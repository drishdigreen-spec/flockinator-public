// Display formatting only. Values are supplied by the caller, not inferred from
// camera motion or battery bars. No flight performance/return calculation.
export function distanceLabel(km){
 if(!Number.isFinite(km)||km<0)return 'D--';
 return km>=100?'D++':'D'+String(Math.floor(km)).padStart(2,'0');
}
export function returnLabel(seconds){
 if(!Number.isFinite(seconds))return 'NR-:--';
 if(seconds<=0)return 'BINGO';
 const value=Math.ceil(seconds);
 return value>599?'NR+:++':'NR'+Math.floor(value/60)+':'+String(value%60).padStart(2,'0');
}

// Authored presentation samples, deliberately unrelated to flight physics or
// mission success. Never use these to decide whether an aircraft can return.
export function sampleReadouts({elapsed=0,index=0,state='SCAN',phase=0}={}){
 if(['CHARGE','STANDBY','ORDERS','APPROVED'].includes(state))return {distanceKm:0,returnSeconds:null};
 if(['NOLINK','EMPTY','CRASH','BLANK'].includes(state)||(state==='ZOOM'&&phase>=10))return {distanceKm:null,returnSeconds:null};
 const age=Math.max(0,elapsed);
 let distanceKm=age<6?0:age<26?1:age<60?2:3;
 if(state==='TAKEOFF'||state==='LAND')distanceKm=0;
 if(state==='R2B')distanceKm=phase<3?2:phase<6?1:0;
 return {distanceKm,returnSeconds:90+index*2-age};
}
