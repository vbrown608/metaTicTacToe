'''
Created on Oct 30, 2013

@author: vbrown
'''

import copy
import logging
import re
from Models import User, Game
 
def nextMove(game, depth, alpha, beta):
    """
    Computes the next move for a player given the current board state and also
    computes if the player will win or not.
 
    Arguments:
        board: list containing X,- and O
        player: one character string 'X' or 'O'
 
    Return Value:
        willwin: 1 if 'X' is in winning state, 0 if the game is draw and -1 if 'O' is
                    winning
        (nextboard, nextcell): position where the player can play the next move so that the
                         player wins or draws or delays the loss
    """
    utility = getUtility(game)
    if depth == 0:
        return utility,(-1,-1)
        
    board = game.metaboard[game.last_cell]
    legalMoves = getLegalMoves(game)
    bestValue = float('-inf')
    bestMove = (-1,-1)
    for board, cell in legalMoves:
        # Move on a copy of the game board.
        tempGame = copy.deepcopy(game)
        tempGame.move(board, cell, tempGame.userX if tempGame.moveX else tempGame.userO)
        val, move = nextMove(tempGame, depth-1, -beta, -alpha)
        val = val*-1
        if val > bestValue:
            bestValue = val
            bestMove = (board, cell)
        # Prune if alpha is greater than beta.
        alpha = max(alpha, val) 
        if alpha >= beta: 
            break
    return bestValue, bestMove
    
def getUtility(game):
    player_coef = 1 if game.moveX else -1
    if game.winner:
        return 1000*player_coef
    mini_win_chances = 0
    for board in game.metaboard:
        mini_win_chances += winChances(board, 'X')
        mini_win_chances -= winChances(board, 'O')
    mini_wins = game.all_mini_wins.count('X') - game.all_mini_wins.count('O')
    meta_win_chances = winChances(game.all_mini_wins, 'X') - winChances(game.all_mini_wins, 'O')
    return (mini_win_chances + mini_wins*10 + meta_win_chances*15)*player_coef
    
def winChances(board, player):
    board = ''.join(board)
    win_chance_patterns = [' XX......', 'X X......', 'XX ......', 
                    '... XX...', '...X X...', '...XX ...', 
                    '...... XX', '......X X', '......XX ', 
                    ' ..X..X..', 'X.. ..X..', 'X..X.. ..', 
                    '. ..X..X.', '.X.. ..X.', '.X..X.. .',
                    '.. ..X..X', '..X.. ..X', '..X..X.. ',
                    ' ...X...X', 'X... ...X', 'X...X... ',
                    '.. .X.X..', '..X. .X..', '..X.X. ..']
    if player == 'O': win_chance_patterns = map(lambda s: s.replace('X','O'), win_chance_patterns)
    wins = map(lambda s: re.compile(s), win_chance_patterns)
    result = 0
    for win in wins:
        if win.match(board): result += 1
    return result
    
    
def getLegalMoves(game): 
    if game.winner:
        return []
    boards = range(9) if game.last_cell == -1 else [game.last_cell]
    result = []
    for board in boards:
        for cell in range(len(game.metaboard[board])):
            if game.metaboard[board][cell] == ' ': result += [(board, cell)]
    return result