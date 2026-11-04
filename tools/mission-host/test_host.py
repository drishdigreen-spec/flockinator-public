import concurrent.futures
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from host import HERE, LABELS, MissionHost


class HostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.library = Path(cls.temp.name)/'world.so'
        subprocess.run(['c++', '-std=c++17', '-shared', '-fPIC', str(HERE/'world.cpp'),
                        '-o', str(cls.library)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.data = tempfile.TemporaryDirectory()
        self.addCleanup(self.data.cleanup)
        self.path = Path(self.data.name)/'mission.json'
        self.game = self.restore()
        self.start = dict(previous=None, start=True, scenario=0, goal=1, seconds=64, repeat=True)

    def restore(self):
        return MissionHost(self.path, self.library, [], [])

    def test_world_survives_absent_fleet_prop_browser_and_process(self):
        req = self.game.submit(self.start)
        epoch = self.game.mission['start_at']
        with patch('host.time.time', return_value=epoch+45):
            first = self.game.snapshot()
            restored = self.restore()
            second = restored.snapshot()
            self.assertEqual(first['nodes'], second['nodes'])
            self.assertEqual(second['status'], 'Running')
            self.assertEqual([n['label'] for n in second['nodes']], LABELS)
            self.assertEqual(len({tuple(n['pose']) for n in second['nodes']}), 16)
            self.assertFalse(second['prop'])
            self.assertIsNone(second['mission']['result'])
            with self.assertRaises(RuntimeError):
                restored.submit(self.start)
            restored.submit(dict(self.start, previous=req, start=False))
            self.assertEqual(self.restore().snapshot()['status'], 'Idle')

    def test_racing_commands_have_one_winner(self):
        def attempt(_):
            try:
                return self.game.submit(self.start)
            except RuntimeError:
                return None
        with concurrent.futures.ThreadPoolExecutor(8) as pool:
            self.assertEqual(sum(bool(v) for v in pool.map(attempt,range(8))), 1)

    def test_one_shot_ends_at_firmware_boundary(self):
        self.game.submit(dict(self.start, repeat=False))
        with patch('host.time.time', return_value=self.game.mission['start_at']+127):
            self.assertEqual(self.game.snapshot()['status'], 'Finished')
            self.assertTrue(all(n['state']=='READY' for n in self.game.snapshot()['nodes']))


if __name__=='__main__':
    unittest.main()
