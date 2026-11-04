{
 const fetchRequest=window.fetch.bind(window);
 window.fetch=async function(input,options={}){
   const headers=new Headers(options.headers);
   if(typeof input==='string'&&input.startsWith('/api/')){
     headers.set('X-Flock-Time',String(Date.now()));
     const pin=sessionStorage.getItem('flock-operator');
     if(options.method==='POST'&&pin)headers.set('X-Flock-Operator',pin);
   }
   let response=await fetchRequest(input,{...options,headers});
   if(response.status===401 && options.method==='POST'){
     const pin=prompt('Enter the operator PIN shown on the Korvo learning-lab screen.');
     if(pin && /^\d{6}$/.test(pin)){sessionStorage.setItem('flock-operator',pin);headers.set('X-Flock-Operator',pin);response=await fetchRequest(input,{...options,headers});}
   }
   return response;
 };
}
