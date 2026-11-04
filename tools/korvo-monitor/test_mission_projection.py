import unittest
from mission_projection import project

class Projection(unittest.TestCase):
    def setUp(self):
        self.s={'v':1,'type':'status','base_mac':'00:11:22:33:44:55','label':'A1',
                'panel':{'world':{'source':'scripted_mission_shared_world','position':[1,-2,3], 'heading':90,'freshness':'LIVE'}},
                'mission':{'source':'scripted_simulation','running':True,'state':'SHARE'}}
    def test_valid(self):
        self.assertEqual(project(0,self.s,self.s['base_mac'],'A1')['position'],(1,-2,3))
    def test_state_validation(self):
        self.assertEqual(project(0,self.s,self.s['base_mac'],'A1')['state'],3)
        self.s['mission']['state']='UNSUPPORTED'
        with self.assertRaises(ValueError): project(0,self.s,self.s['base_mac'],'A1')
    def test_other_world_is_not_mission(self):
        self.s['panel']['world']['source']='host_fictional_survey'
        self.assertIsNone(project(0,self.s,self.s['base_mac'],'A1'))
    def test_bad_values_and_identity(self):
        self.s['panel']['world']['position']=[float('nan'),0,0]
        with self.assertRaises(ValueError): project(0,self.s,self.s['base_mac'],'A1')
        with self.assertRaises(ValueError): project(0,self.s,'00:11:22:33:44:55','A1')
