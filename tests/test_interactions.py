"""Controller tests with an in-memory Pygame shim; no graphical system required."""
from __future__ import annotations
import sys
import types
import unittest
from unittest.mock import Mock

try:
    import pygame
except ImportError:
    pygame = types.ModuleType('pygame')
    sys.modules['pygame'] = pygame

from game import Game
from game_state import GameState
from nasa_api import offline_snapshot


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.g = Game.__new__(Game)
        self.g.state = GameState.fresh(offline_snapshot(),17,seed=188)
        self.g.mode = 'life'
        self.g.modal = None
        self.g.message = ''
        self.g.show_notice = Mock()
        self.g.save = Mock()
        self.g.notice=''
        self.g.notice_time=0

    def test_life_sequence(self):
        g=self.g
        g.use_hotspot('get_sealant')
        self.assertTrue(g.state.progress['life']['tool'])
        for i in range(3):g.use_hotspot(f'fissure_{i}')
        self.assertTrue(all(g.state.progress['life']['fissures']))
        g.use_hotspot('purge')
        self.assertEqual(g.modal,'valve')
        for i in range(3):g.handle_action('valve_turn')
        self.assertTrue(g.state.operational['life'])
        self.assertIsNone(g.modal)

    def test_generator_sequence(self):
        g=self.g;g.mode='generator'
        for spot in ('remove_fuse','get_bridge','install_bridge','grid_console'):
            g.use_hotspot(spot)
        self.assertEqual(g.modal,'grid')
        self.assertEqual(g.state.progress['generator']['stage'],3)
        self.assertIn('puente' not in g.state.inventory,[True])
        g.handle_action('grid_apply')
        self.assertTrue(g.state.operational['generator'])
        self.assertIsNone(g.modal)

    def test_shield_sequence(self):
        g=self.g;g.mode='radiation'
        p=g.state.progress['radiation']
        for index in range(3):
            while p['coils'][index]!=p['targets'][index]:
                g.use_hotspot(f'coil_{index}')
        self.assertEqual(p['coils'],p['targets'])
        g.use_hotspot('shield_switch')
        self.assertTrue(g.state.operational['radiation'])

    def test_hydro_sequence(self):
        g=self.g;g.mode='hydro'
        g.use_hotspot('get_heater')
        self.assertTrue(g.state.progress['hydro']['tool'])
        g.state.progress['hydro']['heat']=3.0
        g.use_hotspot('uv_console')
        self.assertEqual(g.modal,'uv')
        for i in range(3):g.handle_action(f'uv_{i}')
        self.assertTrue(g.state.operational['hydro'])
        self.assertIsNone(g.modal)

if __name__=='__main__':unittest.main()
