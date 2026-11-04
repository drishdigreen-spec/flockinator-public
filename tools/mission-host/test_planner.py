import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from planner import HOME, Planner, routes, new_plan, simulate


class PlannerTests(unittest.TestCase):
    def test_patterns_and_custom_routes_at_edges(self):
        p=new_plan()
        for p['focus'] in ([0,0],[15,11]):
            for p['count'] in (4,8,16):
                for pattern in ('Tree-line fan','Search grid'):
                    p['pattern']=pattern
                    points=[pt for path in routes(p) for pt in path]
                    self.assertEqual(len(set(points)),p['count'] if pattern=='Tree-line fan' else 32)
                    self.assertTrue(all(0<=x<16 and 0<=y<12 for x,y in points))
        p['custom']={'1':[[12,7],[3,4]]}
        self.assertEqual(routes(p)[1],[(12,7),(3,4)])

    def test_reserve_and_high_priority(self):
        p=new_plan()
        p.update(count=16,pattern='Search grid',battery=16)
        p['contacts']=[dict(pos=[8,7],kind='Friendly',priority='High')]
        checked=False
        for seed in range(15):
            p['seed']=seed
            sim=simulate(p,60)
            self.assertTrue(all(u['pos']==HOME and u['energy']>=3 for u in sim['units']))
            self.assertTrue(any(u['reason']=='Return reserve' for u in sim['units']))
            for rs in sim['reports']:
                self.assertEqual(len(rs),len(set(r['unit'] for r in rs)))
            checked |= bool(sim['checks'])
        self.assertTrue(checked)

    def test_shared_clock_and_edits(self):
        with tempfile.TemporaryDirectory() as d, patch('planner.time.time') as clock:
            clock.return_value=100
            f=Path(d)/'test.json'
            board=Planner(f)
            board.submit(dict(revision=0,op='contact',kind='Enemy',priority='High',pos=[3,4]))
            board.submit(dict(revision=1,op='play'))
            clock.return_value=107
            self.assertEqual(Planner(f).snapshot()['sim']['turn'],7)
            board.submit(dict(revision=2,op='pause'))
            clock.return_value=150
            self.assertEqual(board.snapshot()['sim']['turn'],7)
            with self.assertRaises(RuntimeError):
                board.submit(dict(revision=2,op='edit'))
            with self.assertRaises(ValueError):
                board.submit(dict(revision=3,op='erase',pos=[3,4]))
            board.submit(dict(revision=3,op='assess',index=0,outcome='Damaged'))
            board.submit(dict(revision=4,op='edit'))
            self.assertEqual(board.snapshot()['plan']['contacts'][0]['outcome'],'Damaged')
            self.assertEqual(board.snapshot()['sim']['turn'],0)
