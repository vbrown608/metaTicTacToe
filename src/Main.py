"""
Web based Meta Tic-Tac-Toe game for Google App Engine

@author: vbrown
"""

import os
from django.utils import simplejson
from google.appengine.api import channel
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from gaesessions import get_current_session
from Models import User, Game
import Ai

class GameUpdater():
    """Manage all game logic, package game state, and send it to the client"""
    game = None
    
    def __init__(self, game):
        self.game = game
    
    def get_game_message(self):
        """Return a JSON object with the game state"""
        gameUpdate = {
            'metaboard': self.game.metaboard,
            'userX': str(self.game.userX.key().id()),
            'userO': '' if not self.game.userO else str(self.game.userO.key().id()),
            'last_cell': self.game.last_cell,
            'moveX': self.game.moveX,
            'all_mini_wins': self.game.all_mini_wins,
            'winner': self.game.winner,
        }
        return simplejson.dumps(gameUpdate)
    
    def send_update(self):
        """Send the game state, via the channel, to userX and userO"""
        message = self.get_game_message() # Package the game state as a JSON object
        channel.send_message(str(self.game.userX.key().id()) + str(self.game.key()), message)
        if self.game.userO:
            channel.send_message(str(self.game.userO.key().id()) + str(self.game.key()), message)
    
    def check_win(self, board):
        """Check if a board contains three of the same piece in a row. Works on mini or metaboard"""
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
        """Return true iff the move is legal for the given user"""
        if board_num >= 0 and user == self.game.userX or user == self.game.userO:
            if self.game.moveX == (user == self.game.userX): 
                if self.game.metaboard[board_num][cell] == ' ':
                    if (self.game.last_cell == -1 # Forced to move in already full board
                        or self.game.last_cell == board_num): # Normal move: board determined by last cell
                        return True
        return False
    
    def make_move(self, board_num, cell, user):
        """Get a move. If it's legal update the game state, save it, and send it to the client."""
        if self.is_legal_move(board_num, cell, user):
            board = list(self.game.metaboard[board_num])
        
            # Place the move on the board:
            currentPlayer = 'X' if self.game.moveX else 'O'
            board[cell] = currentPlayer
            self.game.metaboard[board_num] = "".join(board)
            
            # Check for a win on the miniboard and the metaboard:
            if self.game.all_mini_wins[board_num] == ' ' and self.check_win(board): 
                self.game.all_mini_wins[board_num] = currentPlayer 
                if self.check_win(self.game.all_mini_wins):
                    self.game.winner = str(user.key().id())
            
            if ' ' in self.game.metaboard[cell]:
                self.game.last_cell = cell
            else:
                self.game.last_cell = -1 # A special case where the miniboard to be played in is full
            self.game.moveX = not self.game.moveX
            self.game.put() # Save the game state
            self.send_update() # Send it to the client
            return

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
        else:
            # No user key stored - make a new one
            self.user = User();
            self.user.put()
            session['user_key'] = str(self.user.key())
            
    def get_user(self):
        return self.user

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
    ('/move', MovePage)], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
