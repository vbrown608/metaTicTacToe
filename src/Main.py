'''
Created on Sep 27, 2013

@author: vbrown
'''

#!/usr/bin/python2.4
#
# Copyright 2010 Google Inc. All Rights Reserved.

# pylint: disable-msg=C6310

"""Channel Tic Tac Toe

This module demonstrates the App Engine Channel API by implementing a
simple tic-tac-toe game.
"""

import logging
import os
import re
from django.utils import simplejson
from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from gaesessions import get_current_session

# Some naming conventions:
# Cell: the index of a cell (0-8)
# Board or miniboard: a string or list representing one of the nine smaller boards
# Board_num: the index of a miniboard (0-8)
# Metaboard: a list of nine miniboards

class User(db.Model):
    google_user = db.BooleanProperty()
    
    def __eq__(self, other):
        return self.key() == other.key()
    
    def __ne__(self, other):
        return self.key() != other.key()
            

class Game(db.Model):
    """All the data we store for a game"""
    userX = db.ReferenceProperty(User, collection_name='userX')
    userO = db.ReferenceProperty(User, collection_name='userO')
    moveX = db.BooleanProperty()
    metaboard = db.StringListProperty()
    last_cell = db.IntegerProperty()
    all_mini_wins = db.StringListProperty()
    winner = db.StringProperty()
    winning_board = db.StringProperty()

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


class GameUpdater():
    game = None
    
    def __init__(self, game):
        self.game = game
    
    def get_game_message(self):
        gameUpdate = {
            'metaboard': self.game.metaboard,
            'userX': str(self.game.userX.key().id()),
            'userO': '' if not self.game.userO else str(self.game.userO.key().id()),
            'moveX': self.game.moveX,
            'all_mini_wins': self.game.all_mini_wins,
            'winner': self.game.winner,
        }
        return simplejson.dumps(gameUpdate)
    
    def send_update(self):
        message = self.get_game_message() # Package the game state as a JSON object
        channel.send_message(str(self.game.userX.key().id()) + str(self.game.key()), message)
        if self.game.userO:
            channel.send_message(str(self.game.userO.key().id()) + str(self.game.key()), message)
    
    def check_win(self, board):
        board = "".join(board)
        if self.game.moveX:
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
        if board_num >= 0 and user == self.game.userX or user == self.game.userO:
            if self.game.moveX == (user == self.game.userX): 
                if self.game.metaboard[board_num][cell] == ' ' and self.game.all_mini_wins[board_num] == ' ':
                    if self.game.metaboard == ['         ']*9 or self.game.last_cell == board_num:
                        return True
        return False
    
    def make_move(self, board_num, cell, user):
        #user = db.get(user)
        if self.is_legal_move(board_num, cell, user):
            board = list(self.game.metaboard[board_num])
        
            # Place the move on the board:
            currentPlayer = 'X' if self.game.moveX else 'O'
            board[cell] = currentPlayer
            self.game.metaboard[board_num] = "".join(board)
            
            # Check for a win on the miniboard and the metaboard:
            if self.check_win(board): 
                self.game.all_mini_wins[board_num] = currentPlayer 
                if self.check_win(self.game.all_mini_wins):
                    self.game.winner = str(user)
            
            self.game.last_cell = cell
            self.game.moveX = not self.game.moveX
            self.game.put() # Save the game state
            self.send_update() # Send it to the client
            return

class GameFromRequest():
    game = None;
    
    def __init__(self, request):
        #user = users.get_current_user() # THIS IS THE BROKEN PART.
        game_key = request.get('g') # The client passes the game key back in order to open up the channel
        if game_key:
            self.game = db.get(db.Key(game_key)) #Game.get_by_key_name(game_key)
    
    def get_game(self):
        return self.game


class MovePage(webapp.RequestHandler):
    def post(self):
        game = GameFromRequest(self.request).get_game()
        session = get_current_session()
        user_key = session.get('user_key')
        user = db.get(db.Key(user_key))
        if game and user:
            board_num = int(self.request.get('i'))
            cell = int(self.request.get('j'))
            GameUpdater(game).make_move(board_num, cell, user)
    
    
class OpenedPage(webapp.RequestHandler):
    def post(self):
        game = GameFromRequest(self.request).get_game()
        GameUpdater(game).send_update()

class NewGame(webapp.RequestHandler):
    def get(self):
        session = get_current_session()
        user_key = session.get('user_key')
        #game_key = str(user_key) # Game key gets created here - same user X's user id.
        game = Game(#key_name = game_key,
                    userX = db.get(db.Key(user_key)),
                    moveX = True,
                    all_mini_wins = [' ']*9,
                    metaboard = ['         ']*9)
        game.put()
        self.redirect('/game?g=' + str(game.key()))

class GamePage(webapp.RequestHandler):
    """Renders a page representing a single game"""
    
    def get(self):
        """Renders the main page. When this page is shown, we create a new
        channel to push asynchronous updates to the client."""
        session = get_current_session()
        user_key = session.get('user_key')
        
        if user_key: 
            user = db.get(db.Key(user_key))
        else:
            user = User()
            user.put()
            session['user_key'] = str(user.key())
            user_key = str(user.key())

        game_key = self.request.get('g')
        game = db.get(db.Key(game_key))
        if user != game.userX and not game.userO:
            game.userO = user
            game.put()

        game_link = 'http://localhost:8080/game?g=' + game_key

        if game:
            token = channel.create_channel(str(user.key().id()) + game_key)
            template_values = {'token': token,
                               'me': user.key().id(),
                               'nickname': user.key().id(),
                               'game_key': game_key,
                               'game_link': game_link,
                               'initial_message': GameUpdater(game).get_game_message()
                              }
            path = os.path.join(os.path.dirname(__file__), 'game.html')

            self.response.out.write(template.render(path, template_values))
        else:
            self.response.out.write('No such game')

            
class MainPage(webapp.RequestHandler):
    """ Render the main landing page where users can view their current games or create a new one."""
    
    def get(self):
        session = get_current_session()
        user_key = session.get('user_key')
        if not user_key:
            user = User()
            user.put()
            session['user_key'] = str(user.key())
        
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/new', NewGame),
    ('/game', GamePage),
    ('/opened', OpenedPage),
    ('/move', MovePage)], debug=True)


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
