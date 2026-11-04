import unittest
from bridge import status_frame

class Frames(unittest.TestCase):
    def test_valid(self):
        status = dict(v=1, type='status', base_mac='00:11:22:33:44:55', label='A1', firmware='0.10.1', uptime_ms=123456, free_internal=2048)
        self.assertEqual(status_frame(0, status, status['base_mac'], 'A1'), b'F1 0 1 0.10.1 123 2\n')
        for key, value in [('label', 'A2'), ('base_mac', '02:00:00:00:00:02'), ('firmware', 'bad\nline'), ('uptime_ms', -1), ('free_internal', True)]:
            bad = dict(status, **{key: value})
            with self.assertRaises(ValueError): status_frame(0, bad, status['base_mac'], 'A1')
    def test_long_uptime(self):
        status = dict(v=1, type='status', base_mac='00:11:22:33:44:55', label='A1', firmware='0.10.1', uptime_ms=6000000000, free_internal=2048)
        self.assertIn(b'6000000', status_frame(0, status, status['base_mac'], 'A1'))
        status['uptime_ms'] = 0x100000000 * 1000
        with self.assertRaises(ValueError): status_frame(0, status, status['base_mac'], 'A1')

    def test_missing(self):
        with self.assertRaises(ValueError): status_frame(0, {}, '00:11:22:33:44:55', 'A1')


class Polling(unittest.TestCase):
    def test_world_frame_includes_reported_state(self):
        from bridge import poll
        from unittest.mock import Mock
        row={'factory_base_mac':'00:11:22:33:44:55','label':'A1'}
        client=Mock();client.request.return_value=dict(v=1,type='status',base_mac=row['factory_base_mac'],label='A1',firmware='0.10.1',uptime_ms=0,free_internal=2048,panel={'world':{'source':'scripted_mission_shared_world','position':[1,-2,0], 'heading':90,'freshness':'LIVE'}},mission={'source':'scripted_simulation','running':True,'state':'SHARE'})
        self.assertIn(b'P2 0 10 -20 90 1 1 3\n',poll(0,row,client))
    def test_failure_states(self):
        from bridge import poll
        from unittest.mock import Mock
        import urllib.error
        row = {'factory_base_mac':'00:11:22:33:44:55', 'label':'A1'}
        self.assertEqual(poll(0, row, None), b'F1 0 2 - 0 0\n')
        client = Mock()
        client.request.side_effect = TimeoutError()
        self.assertEqual(poll(0, row, client), b'F1 0 0 - 0 0\n')
        client.request.side_effect = urllib.error.HTTPError('local', 401, 'Unauthorized', {}, None)
        self.assertEqual(poll(0, row, client), b'F1 0 2 - 0 0\n')
        client.request.side_effect = None
        client.request.return_value = {'v':1, 'type':'status', 'base_mac':'wrong'}
        self.assertEqual(poll(0, row, client), b'F1 0 2 - 0 0\n')
        self.assertEqual(client.request.call_args.args, ('GET', '/v1/status'))

if __name__ == "__main__": unittest.main()
