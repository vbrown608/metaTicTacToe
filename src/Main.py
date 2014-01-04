"""
Web based Meta Tic-Tac-Toe game for Google App Engine.
This file controls the server-side interaction including
    -creating and storing Users and Games
    -managing game play
    -serving pages
    
User identity is managed by browser cookies using gaesessions.
Game updates are pushed to users via the Google Channel API.

Datastore models (User and Game) are defined in Models.py
AI strategy is defined in Ai.py

Created 2013
@author: vbrown
"""

import os
import logging
import json
from google.appengine.api import channel
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from gaesessions import get_current_session
from Models import User, Game
import Ai

AI_ID = 1002 # The computer player (AI) is represented by a special user in the datastore.
# Using 6192449487634432 for dev appserver.

class GameUpdater():
    """Manage all game logic, package game state, and send it to the client"""
    game = None
    
    def __init__(self, game):
        self.game = game
    
    def get_game_message(self):
        """Return a JSON object describing the game state"""
        gameUpdate = {
            "metaboard": self.game.metaboard,
            "userX": str(self.game.userX.key().id()),
            "userO": '' if not self.game.userO else str(self.game.userO.key().id()),
            "last_cell": self.game.last_cell,
            "moveX": self.game.moveX,
            "all_mini_wins": self.game.all_mini_wins,
            "winner": self.game.winner,
        }
        return json.dumps(gameUpdate)
    
    def send_update(self):
        """Send the game state, via the channel, to userX and userO"""
        message = self.get_game_message() # Package the game state as a JSON object
        channel.send_message(str(self.game.userX.key().id()) + str(self.game.key()), message)
        if self.game.userO:
            channel.send_message(str(self.game.userO.key().id()) + str(self.game.key()), message)
    
    def make_move(self, board_num, cell, user):
        """Get a move. If it's legal update the game state, save it, and send it to the client."""
        if self.game.move(board_num, cell, user):
            self.game.put() # Save the game state
            self.send_update() # Send it to the client
        if self.game.userO == User.get_by_id(AI_ID): # Check if player O is AI - need to fix the check
            board_num, cell = Ai.nextMove(self.game)
            if self.game.move(board_num, cell, self.game.userO):
                self.game.put()
                self.send_update()

class GameFromRequest():
    """Take a request with variable g (the game key) and return the game entity from the datastore"""
    game = None;
    
    def __init__(self, request):
        game_id = request.get('g') # The client passes the game key back in order to open up the channel
        if game_id:
            self.game = Game.get_by_id(int(game_id))
    
    def get_game(self):
        return self.game
    
class UserFromSession():
    """Take the session, get the user key, and return the user object.
    If no user if set yet, create a new user, store in datastore, set cookie, and return that user"""
    user = None;
    
    def __init__(self, session):
        user_key = session.get('user_key')
        if user_key:
            self.user = db.get(db.Key(user_key))
        if not self.user:
            # No user key stored - make a new one
            self.user = User();
            self.user.put()
            session['user_key'] = str(self.user.key())
            
    def get_user(self):
        return self.user
    
class PlayAi(webapp.RequestHandler):
    """Add the Ai agent as player O and begin game play"""
    def post(self):
        game = GameFromRequest(self.request).get_game()
        ai = User.get_by_id(AI_ID)
        if not ai:
            logging.info('Failed to retrieve AI user')
        if not game.userO:
            game.userO = User.get_by_id(AI_ID)
            game.put()
            GameUpdater(game).send_update()
        
class MovePage(webapp.RequestHandler):
    """Handle a game move from the client"""
    def post(self):
        game = GameFromRequest(self.request).get_game()
        user = UserFromSession(get_current_session()).get_user()
        if game and user:
            board_num = int(self.request.get('i'))
            cell = int(self.request.get('j'))
            GameUpdater(game).make_move(board_num, cell, user)
    
class OpenedPage(webapp.RequestHandler):
    """A game page has been opened and the channel has been established. 
    The client sends a post with the game id and the server send back the the game state."""
    def post(self):
        game = GameFromRequest(self.request).get_game()
        GameUpdater(game).send_update()

class NewGame(webapp.RequestHandler):
    """Create a new game and then redirect the client to that game."""
    def post(self):
        user = UserFromSession(get_current_session()).get_user()
        game = Game(userX = user,
                    moveX = True,
                    last_cell = -1,
                    all_mini_wins = [' ']*9,
                    metaboard = ['         ']*9)
        game.put()
        self.redirect('/game?g=' + str(game.key().id()))

class GamePage(webapp.RequestHandler):
    """Render a page representing a single game"""
    
    def get(self):
        """Renders the main page. When this page is shown, we create a new
        channel to push asynchronous updates to the client."""
        
        user = UserFromSession(get_current_session()).get_user()
        game = GameFromRequest(self.request).get_game()
        
        # Assign player O
        if user != game.userX and not game.userO:
            game.userO = user
            game.put()

        if game:
            token = channel.create_channel(str(user.key().id()) + str(game.key()))
            template_values = {'token': token,
                               'me': user.key().id(),
                               'my_piece': 'X' if game.userX == user else 'O', 
                               'game_id': str(game.key().id()),
                               'game_link': self.request.url,
                               'initial_message': GameUpdater(game).get_game_message()
                              }
            path = os.path.join(os.path.dirname(__file__), 'game.html')

            self.response.out.write(template.render(path, template_values))
        else:
            self.response.out.write('No such game')
            
class AboutPage(webapp.RequestHandler):
    """Render a page with some background info about the game"""
    def get(self):
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'about.html')
        self.response.out.write(template.render(path, template_values))
            
class MainPage(webapp.RequestHandler):
    """Render the main landing page where users can view instructions and create a new one."""
    def get(self):
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/about', AboutPage),
    ('/new', NewGame),
    ('/game', GamePage),
    ('/opened', OpenedPage),
    ('/ai', PlayAi),
    ('/move', MovePage)], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
