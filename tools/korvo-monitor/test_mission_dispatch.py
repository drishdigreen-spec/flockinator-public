import json
import unittest
from mission_dispatch import dispatch

class Fake:
    def __init__(self, mac, label): self.mac=mac; self.label=label; self.run=12; self.running=False
    def request(self, method, path, body=b'', timeout=0):
        if method=='POST':
            c=json.loads(body); self.run=c['run']; self.running=c['op']=='mission_start'; return {'ok':True}
        return {'type':'status','v':1,'base_mac':self.mac,'label':self.label,'mission':{'source':'scripted_simulation','run':self.run,'running':self.running,'waiting':False}}
class Tests(unittest.TestCase):
    def test_start_stop_and_failed_node(self):
        rows=[{'factory_base_mac':f'AA:BB:CC:DD:EE:{i:02X}','label':f'{chr(65+i//4)}{1+i%4}'} for i in range(16)]
        clients=[Fake(r['factory_base_mac'],r['label']) for r in rows]; clients[2]=None
        run,result=dispatch(True,0,1,64,True,rows,clients)
        self.assertEqual(sum(result),15); self.assertEqual(clients[0].run,run)
        _,result=dispatch(False,0,1,64,True,rows,clients)
        self.assertEqual(sum(result),15); self.assertFalse(clients[0].running)

    def test_delayed_status_publication(self):
        class Delayed(Fake):
            def __init__(self,mac,label): super().__init__(mac,label); self.previous=None; self.lag=0
            def request(self,method,path,body=b'',timeout=0):
                if method=='POST':
                    self.previous=(self.run,self.running); result=super().request(method,path,body,timeout); self.lag=1; return result
                value=super().request(method,path,body,timeout)
                if self.lag:
                    self.lag-=1; value['mission']['run'],value['mission']['running']=self.previous
                return value
        rows=[{'factory_base_mac':f'AA:BB:CC:DD:EE:{i:02X}','label':f'{chr(65+i//4)}{1+i%4}'} for i in range(16)]
        clients=[Delayed(r['factory_base_mac'],r['label']) for r in rows]
        _,results=dispatch(True,0,0,64,True,rows,clients)
        self.assertEqual(sum(results),16)
