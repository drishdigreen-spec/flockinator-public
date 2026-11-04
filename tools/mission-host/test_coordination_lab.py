import unittest
from coordination_lab import experiment, learning_comparison, mission_comparison, random_scenario


class CommunicationLabTests(unittest.TestCase):
    def test_scramble_changes_payloads_but_not_delivery_or_world(self):
        data=learning_comparison(11,'Scrambled')
        clear,scrambled,restored,_=data['rows']
        self.assertEqual(clear['packets'],scrambled['packets'])
        self.assertEqual(clear['accurate'],scrambled['accurate'])
        self.assertEqual(clear['training_packets'],restored['training_packets'])
        self.assertEqual(len(data['replay']),clear['decisions'])
        for pair in data['replay']:
            a,b=pair['clear'],pair['impaired']
            for key in ('round','unit','cue','truth'):
                self.assertEqual(a[key],b[key])
            self.assertEqual([m['sender'] for m in a['messages']],[m['sender'] for m in b['messages']])
        self.assertEqual(clear['recoveries'],sum(clear['by_round']))
        self.assertGreater(clear['accurate'],restored['accurate'])
        self.assertGreater(clear['recoveries'],scrambled['recoveries'])

    def test_muted_learners_cannot_use_hidden_peer_information(self):
        result=learning_comparison(90,'Muted')
        clear,muted,restored,both=result['rows']
        self.assertEqual(restored['known'],0)
        self.assertEqual(muted['packets'],0)
        for row in (muted,restored,both):
            self.assertEqual(row['by_round'],result['solo']['by_round'])
        self.assertEqual(clear['decisions'],512)

    def test_planner_counterfactual_and_null_result(self):
        for seed,change in ((11,2),(90,0)):
            p=random_scenario(seed)
            v=mission_comparison(p)
            self.assertEqual(v['clear']['correct']-v['muted']['correct'],change)
            self.assertEqual(v['muted']['delivered'],0)
            self.assertEqual(v['clear']['home'],p['count'])
        with self.assertRaises(ValueError):
            experiment(dict(seed=True,link='Muted',board='Seeded'),{})

    def test_reproducible_partial_loss(self):
        result=learning_comparison(7,'Half lost')
        self.assertEqual(result,learning_comparison(7,'Half lost'))
        clear,impaired,*_=result['rows']
        self.assertTrue(0<impaired['packets']<clear['packets'])
