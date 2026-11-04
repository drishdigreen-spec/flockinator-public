import json
import unittest
from mission_commands import command

class MissionCommands(unittest.TestCase):
    def test_start_and_stop(self):
        self.assertEqual(json.loads(command(True, 42))['op'], 'mission_start')
        self.assertEqual(json.loads(command(False, 42))['run'], 42)
        self.assertEqual(json.loads(command(False, 42))['op'], 'mission_stop')
    def test_invalid(self):
        for kwargs in ({'run':-1}, {'run':1,'seconds':65}, {'run':1,'scenario':3}, {'run':True}, {'run':1,'repeat':1}):
            with self.assertRaises(ValueError): command(True, **kwargs)
