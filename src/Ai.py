'''
Created on Oct 30, 2013

@author: vbrown
'''

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
    #gameInfo = 'D=' + str(depth) + ' Util=' + str(bestValue) + ' MoveX=' + str(game.moveX) + ' M=' + str(bestMove)
    #logging.info(gameInfo)
    return bestValue, bestMove
    
def getUtility(game):
    player_coef = 1 if game.moveX else -1
    if game.winner:
        return float('inf')*player_coef
    else:
        return (game.all_mini_wins.count('X') - game.all_mini_wins.count('O'))*player_coef
    
def getLegalMoves(game):
    boards = range(9) if game.last_cell == -1 else [game.last_cell]
    result = []
    for board in boards:
        for cell in range(len(game.metaboard[board])):
            if game.metaboard[board][cell] == ' ': result += [(board, cell)]
    return result