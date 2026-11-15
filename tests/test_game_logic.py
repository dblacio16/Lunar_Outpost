"""Offline unit tests for version 1; do not require the Pygame window or internet."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from game_state import GameState,clean_allocation,clamp
from nasa_api import fetch_donki,read_cache,offline_snapshot,KINDS
from nasa_simulation import calculate_risk,sample_info,flare_weight
from event_manager import pick_event,resolve_event
from interactables import room_hotspots

SAMPLES={
 'FLR':[{'flrID':'test-flr','beginTime':'2026-05-01T01:20Z','classType':'M5.5'}],
 'GST':[{'gstID':'test-gst','startTime':'2026-05-01T05:00Z','allKpIndex':[{'kpIndex':6.0}]}],
 'SEP':[{'sepID':'test-sep','eventTime':'2026-05-01T06:00Z'}],
 'CME':[{'activityID':'test-cme','startTime':'2026-05-01T07:00Z','cmeAnalyses':[{'speed':850}]}],
}

class GameLogicTests(unittest.TestCase):
    def snapshot(self):return {'source':'NASA DONKI','mode':'online','fetched_at':'2026-05-01T08:00:00+00:00',
                                'events':SAMPLES,'error':''}

    def test_risk_and_science_immutable(self):
        copy=json.dumps(SAMPLES,sort_keys=True)
        risk=calculate_risk(SAMPLES)
        self.assertGreater(risk,15)
        self.assertLessEqual(risk,100)
        self.assertEqual(copy,json.dumps(SAMPLES,sort_keys=True))
        self.assertIn('Kp',sample_info('GST',SAMPLES['GST'][0])['detail'])
        self.assertLess(flare_weight('C2.0'),flare_weight('X2.0'))
        self.assertEqual(calculate_risk({k:[] for k in KINDS}),0)

    def test_offline_cannot_fake_measurements(self):
        no=offline_snapshot()
        self.assertEqual(no['mode'],'offline')
        self.assertTrue(all(not v for v in no['events'].values()))

    def test_nasa_four_endpoints_with_mocked_https(self):
        called=[]
        def fake_get(url, params, timeout):
            kind=url.rsplit('/',1)[-1]; called.append(kind)
            self.assertTrue(url.startswith('https://api.nasa.gov/'))
            self.assertIn('api_key',params)
            self.assertEqual(timeout,5)
            obj=Mock();obj.json=lambda:SAMPLES[kind];obj.raise_for_status=lambda:None
            return obj
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'cache.json'
            data=fetch_donki(path,force=True,get=fake_get)
            self.assertEqual(data['mode'],'online')
            self.assertEqual(called,list(KINDS))
            cached=read_cache(path)
            self.assertEqual(cached['mode'],'cache')
            self.assertEqual(data['events'],cached['events'])
            self.assertEqual(fetch_donki(path,force=False,get=lambda **_:self.fail()),cached)

    def test_nasa_empty_and_invalid_response(self):
        def empty(url,params,timeout):
            out=Mock();out.raise_for_status=lambda:None;out.json=lambda:[]
            return out
        def invalid(url,params,timeout):
            out=Mock();out.raise_for_status=lambda:None;out.json=lambda:{'error':'unavailable'}
            return out
        with tempfile.TemporaryDirectory() as folder:
            valid=fetch_donki(Path(folder)/'empty.json',force=True,get=empty)
            self.assertEqual(sum(map(len,valid['events'].values())),0)
            bad=fetch_donki(Path(folder)/'bad.json',force=True,get=invalid)
            self.assertEqual(bad['mode'],'offline')

    def test_new_games_differ_without_modifying_nasa(self):
        a=GameState.fresh(self.snapshot(),calculate_risk(SAMPLES),seed=123)
        b=GameState.fresh(self.snapshot(),calculate_risk(SAMPLES),seed=456)
        self.assertNotEqual(a.resources,b.resources)
        self.assertEqual(a.science['events'],b.science['events'])
        self.assertEqual(a.seed,123)
        self.assertEqual(a.sol,1)
        self.assertEqual(a.risk,b.risk)

    def test_allocation_never_exceeds_100(self):
        self.assertRaises(ValueError,clean_allocation,{'life':60,'hydro':30,'radiation':20})
        self.assertEqual(sum(clean_allocation({'life':30,'hydro':25,'radiation':20}).values()),75)
        state=GameState.fresh(self.snapshot(),25,seed=30)
        self.assertFalse(state.configure_allocation({'life':5,'hydro':5,'radiation':90}))
        self.assertTrue(state.configure_allocation({'life':35,'hydro':30,'radiation':25}))

    def test_interaction_steps_and_repairs(self):
        state=GameState.fresh(self.snapshot(),25,seed=30)
        self.assertEqual(room_hotspots(state,'life')[0].key,'get_sealant')
        state.progress['life']['tool']=True
        self.assertEqual(len(room_hotspots(state,'life')),3)
        state.progress['life']['fissures']=[True,True,True]
        self.assertEqual(room_hotspots(state,'life')[0].key,'purge')
        state.repair('life')
        self.assertTrue(state.operational['life'])
        self.assertEqual(room_hotspots(state,'life'),[])
        state.reset_room('life')
        self.assertFalse(state.operational['life'])
        self.assertEqual(state.progress['life']['valve'],0)

    def test_persistent_state_and_player(self):
        state=GameState.fresh(self.snapshot(),24,seed=77)
        state.player_x=647.0
        state.current_scene='hydro'
        state.progress['hydro']['tool']=True
        state.inventory.append('calentador')
        state.progress['hydro']['heat']=2.3
        state.pending_event={'kind':'freeze','title':'test','body':'test','broken':'hydro',
                             'choices':[('a','food',-2,'energy',1),('b','energy',-2,'life',1)]}
        with tempfile.TemporaryDirectory() as folder:
            f=Path(folder)/'save.json';state.save(f)
            loaded=GameState.load(f)
            self.assertEqual(loaded.player_x,647.0)
            self.assertEqual(loaded.current_scene,'hydro')
            self.assertEqual(loaded.progress['hydro']['heat'],2.3)
            self.assertEqual(loaded.science,state.science)
            self.assertIsNotNone(loaded.pending_event)

    def test_sols_bounded_and_victory(self):
        state=GameState.fresh(self.snapshot(),12,seed=9)
        for r in ('life','generator','radiation','hydro'):state.repair(r)
        state.configure_allocation({'life':35,'hydro':30,'radiation':25})
        for sol in range(29):
            self.assertTrue(state.advance_sol())
        self.assertTrue(state.won)
        self.assertEqual(state.sol,30)
        self.assertFalse(state.advance_sol())

    def test_game_over_at_zero_and_limits(self):
        s=GameState.fresh(self.snapshot(),25,seed=6)
        s.adjust(life=-500)
        self.assertTrue(s.lost)
        self.assertEqual(s.resources['life'],0)
        self.assertEqual(clamp(120),100)
        self.assertEqual(clamp(-2),0)

    def test_event_has_real_consequences(self):
        s=GameState.fresh(self.snapshot(),100,seed=91)
        event={'kind':'solar','title':'test','body':'test','broken':'radiation',
               'choices':[('Reforzar','energy',-7,'integrity',3),('Riesgo','integrity',-7,'food',2)]}
        s.pending_event=event
        before=s.resources.copy()
        self.assertTrue(resolve_event(s,0))
        self.assertLess(s.resources['energy'],before['energy'])
        self.assertGreater(s.resources['integrity'],before['integrity'])
        self.assertEqual(len(s.choices),1)
        self.assertIsNone(s.pending_event)

    def test_event_picker_deterministic_for_seed_and_sol(self):
        a=GameState.fresh(self.snapshot(),90,seed=222)
        b=GameState.fresh(self.snapshot(),90,seed=222)
        self.assertEqual(pick_event(a),pick_event(b))

if __name__=='__main__':unittest.main()
