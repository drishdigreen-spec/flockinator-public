import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import bridge

class Port:
    def __init__(self, **kw): self.writes=[]; self.input=[b'MC1 1 1 0 0 64 1\n']
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read_until(self,*args): return b'KORVO1 00:11:22:33:44:55\n'
    def write(self,data): self.writes.append(data)
    def read(self,n): return self.input.pop(0) if self.input else b''

class TestBridge(unittest.TestCase):
    def test_usb_command_dispatch_and_result(self):
        port=Port()
        with tempfile.TemporaryDirectory() as d, \
             patch.object(bridge.Path,'home',return_value=Path(d)), \
             patch.object(bridge.serial,'Serial',return_value=port), \
             patch.object(bridge,'management_key',return_value=b'x'*32), \
             patch.object(bridge,'NetworkClient',return_value=object()), \
             patch.object(bridge,'poll',side_effect=lambda i,row,client:f'F1 {i} 0 - 0 0\n'.encode()), \
             patch.object(bridge,'dispatch',return_value=(7,[True]*15+[False])) as dispatch, \
             patch('sys.argv',['bridge','--seconds','1']):
            bridge.main()
        self.assertTrue(dispatch.called)
        self.assertIn(b'R1 1 0 0 16\n',port.writes)
        self.assertIn(b'R1 1 1 15 1\n',port.writes)
