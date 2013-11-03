'''
Created on Nov 1, 2013

@author: vbrown
'''

import os
import re
from google.appengine.ext import db

# Some naming conventions:
# Cell: the index of a cell (0-8)
# Board or miniboard: a string or list representing one of the nine smaller boards
# Board_num: the index of a miniboard (0-8)
# Metaboard: a list of nine miniboards

class User(db.Model):
    """Represent a user of the application. Equivalent to a browser session."""
    google_user = db.BooleanProperty()
    
    def __eq__(self, other):
        return self.key() == other.key()
    
    def __ne__(self, other):
        return self.key() != other.key()        

class Game(db.Model):
    """Represent a single game of meta-tic-tac-toe"""
    userX = db.ReferenceProperty(User, collection_name='userX')
    userO = db.ReferenceProperty(User, collection_name='userO')
    moveX = db.BooleanProperty()
    metaboard = db.StringListProperty()
    last_cell = db.IntegerProperty()
    all_mini_wins = db.StringListProperty()
    winner = db.StringProperty()
    winning_board = db.StringProperty()
    
    def check_win(self, board):
        """Check if a board contains three of the same piece in a row. Works on mini or metaboard"""
        board = "".join(board)
        if self.moveX:
            # X just moved, check for X wins
            wins = Wins().x_wins
        else:
            # O just moved, check for O wins
            wins = Wins().o_wins
        for win in wins:
            if win.match(board):
                return True
        return False
        
    def is_legal_move(self, board_num, cell, user):
        """Return true iff the move is legal for the given user"""
        if board_num >= 0 and user == self.userX or user == self.userO:
            if self.game.moveX == (user == self.userX): 
                if self.metaboard[board_num][cell] == ' ':
                    if (self.last_cell == -1 # Forced to move in already full board
                        or self.last_cell == board_num): # Normal move: board determined by last cell
                        return True
        return False
    
    def move(self, board_num, cell, user):
        """Get a move. If it's legal update the game state"""
        if self.is_legal_move(board_num, cell, user):
            board = list(self.metaboard[board_num])
        
            # Place the move on the board:
            currentPlayer = 'X' if self.moveX else 'O'
            board[cell] = currentPlayer
            self.metaboard[board_num] = "".join(board)
            
            # Check for a win on the miniboard and the metaboard:
            if self.all_mini_wins[board_num] == ' ' and self.check_win(board): 
                self.all_mini_wins[board_num] = currentPlayer 
                if self.check_win(self.all_mini_wins):
                    self.game.winner = str(user.key().id())
            
            if ' ' in self.game.metaboard[cell]:
                self.game.last_cell = cell
            else:
                self.last_cell = -1 # A special case where the miniboard to be played in is full

            self.moveX = not self.moveX
            return

class Wins():
    """Store all possible miniboard wins as a list of strings, for pattern matching later on."""
    x_win_patterns = ['XXX......',
                    '...XXX...',
                    '......XXX',
                    'X..X..X..',
                    '.X..X..X.',
                    '..X..X..X',
                    'X...X...X',
                    '..X.X.X..']
    
    o_win_patterns = map(lambda s: s.replace('X','O'), x_win_patterns)
    
    x_wins = map(lambda s: re.compile(s), x_win_patterns)
    o_wins = map(lambda s: re.compile(s), o_win_patterns)
