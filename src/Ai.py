'''
Created on Oct 30, 2013

@author: vbrown
'''

import os
import re
import copy
import logging
from Models import User, Game
 
def nextMove(game, depth):
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
    if game.check_win(str(game.all_mini_wins)):
        if game.moveX: return float('-inf'),(-1,-1)
        else: return float('inf'),(-1,-1)
    if depth <= 0:
        return 0,(-1,-1)
        
    res_list = [] # list for appending the resulting tuples
    board = game.metaboard[game.last_cell]
    c = board.count(' ')
    if  c is 0:
        return 0,-1
    legalMoves = getLegalMoves(game)
    for board, cell in legalMoves:
        # Move on a copy of the game board
        tempGame = copy.deepcopy(game)
        tempGame.move(board, cell, 'X' if tempGame.moveX else 'O')
        ret,move=nextMove(tempGame, depth-1)
        res_list.append(ret)
    if game.moveX:
        maxele=max(res_list)
        return maxele,legalMoves[res_list.index(maxele)]
    else :
        minele=min(res_list)
        return minele,legalMoves[res_list.index(minele)]
    
def ultility(game):
    pass
    
def getLegalMoves(game):
    boards = range(9) if game.last_cell == -1 else [game.last_cell]
    result = []
    for board in boards:
        for cell in range(len(game.metaboard[board])):
            if game.metaboard[board][cell] == ' ': result += [(board, cell)]
    return result