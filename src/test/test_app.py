'''
Created on Nov 1, 2013

@author: vbrown
'''

import unittest
import logging
from Models import User, Game
from Ai import *

class Test(unittest.TestCase):
    def test_legal_moves(self):
        userX = User()
        userX.put()
        myGame = Game(userX,
                    moveX = True,
                    last_cell = 1,
                    all_mini_wins = [' ']*9,
                    metaboard = ['         ']*9)
        legal_moves = getLegalMoves(myGame)
        self.assert_(legal_moves == [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8)], msg=str(legal_moves))
    
    def test_ai(self):
        userX = User()
        userX.put()
        myGame = Game(userX,
                    moveX = True,
                    last_cell = 4,
                    all_mini_wins = [' ']*9,
                    metaboard = ['         ']*9)
        result = nextMove(myGame, 3)
        self.assertEqual(result, (0, (4, 0)))