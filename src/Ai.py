'''
Created on Oct 30, 2013

@author: vbrown
'''

import os
import re
import copy
import logging
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
    if utility > 100 or depth <= 0:
        if game.moveX: return utility*-1,(-1,-1)
        else: return utility,(-1,-1)
        
    res_list = [] # list for appending the resulting tuples
    board = game.metaboard[game.last_cell]
    c = board.count(' ')
    if  c is 0:
        return 0,-1
    legalMoves = getLegalMoves(game)
    for board, cell in legalMoves:
        # Move on a copy of the game board.
        tempGame = copy.deepcopy(game)
        tempGame.move(board, cell, 'X' if tempGame.moveX else 'O')
        val,move=nextMove(tempGame, depth-1, -beta, -alpha)
        val = val*-1
        res_list.append(val)
        
        # Prune if alpha is greater than beta.
        alpha = max(alpha, val)
        if alpha >= beta: 
            logging.info("PRUNING AT DEPTH " + str(depth))
            break
    maxele=max(res_list)
    return maxele,legalMoves[res_list.index(maxele)]
    
def getUtility(game):
    if game.winner:
        return float('inf'), (-1,-1)
    return (game.all_mini_wins.count('X') - game.all_mini_wins.count('O'))
    
def getLegalMoves(game):
    boards = range(9) if game.last_cell == -1 else [game.last_cell]
    result = []
    for board in boards:
        for cell in range(len(game.metaboard[board])):
            if game.metaboard[board][cell] == ' ': result += [(board, cell)]
    return result