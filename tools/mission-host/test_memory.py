from datetime import datetime
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from exercise_memory import deliver_one
from planner import HOME, Planner, random_scenario, distance, simulate


class MemoryTests(unittest.TestCase):
    def test_draws_cover_sparse_crowded_empty_and_unreachable(self):
        sizes=set()
        beyond=False
        for seed in range(150):
            p=random_scenario(seed)
            self.assertEqual(p,random_scenario(seed))
            tiles=[tuple(c['pos']) for c in p['contacts']]
            self.assertEqual(len(tiles),len(set(tiles)))
            self.assertNotIn(HOME,tiles)
            sizes.add(len(tiles))
            beyond |= any(2*distance(t,HOME)+3>p['battery'] for t in tiles)
        self.assertTrue(0 in sizes and 1 in sizes and 24 in sizes and beyond)

    def test_archive_timestamps_restart_dedup_and_card_readback(self):
        with tempfile.TemporaryDirectory() as tmp, patch('planner.time.time') as clock:
            clock.return_value=1700000000
            path=Path(tmp)/'planner.json'
            board=Planner(path)
            def cmd(op,**kw):
                board.submit(dict(op=op,revision=board.plan['revision'],**kw))
            cmd('randomize',seed=8)
            cmd('play')
            episode=board.plan['episode']
            clock.return_value+=2
            cmd('pause')
            board.checkpoint()
            board=Planner(path)
            clock.return_value+=120
            cmd('play')
            clock.return_value+=90
            board.checkpoint()
            old=board.download(episode)
            cmd('edit')
            self.assertEqual(board.download(episode),old)
            with ZipFile(BytesIO(old)) as archive:
                events=[json.loads(line) for line in archive.read('A1.jsonl').splitlines()]
                self.assertEqual([e['seq'] for e in events],list(range(1,len(events)+1)))
                self.assertEqual(events[-1]['event'],'landed')
                a,b=[next(e for e in events if e['turn']==t) for t in (2,3)]
                dt=lambda e:datetime.fromisoformat(e['utc'])
                self.assertEqual((dt(b)-dt(a)).total_seconds(),121)
                self.assertFalse(any('ground_truth' in e for e in events))
            class Card:
                mac='test'
                def request(self,method,path,payload,timeout):
                    self.data=payload
                    return dict(ok=True,sha256=sha256(payload).hexdigest(),bytes=len(payload))
                def read_journal(self,digest):
                    return self.data
            card=Card()
            with patch.object(card,'read_journal',return_value=b'wrong'),self.assertRaises(ValueError):
                deliver_one(board.archive_dir,episode,'A1',card)
            self.assertFalse(board.journals()[0]['verified'])
            self.assertTrue(deliver_one(board.archive_dir,episode,'A1',card))
            self.assertEqual(board.journals()[0]['verified'],['A1'])

    def test_paired_messages_and_no_truth_leakage(self):
        for seed in range(100):
            events=[]
            simulate(random_scenario(seed),60,events)
            sent=[e[3] for e in events if e[2]=='message_sent']
            if sent:
                self.assertEqual(sent,[e[3] for e in events if e[2]=='message_received'])
                break
        else:
            self.fail('No independent checks in test scenarios')
