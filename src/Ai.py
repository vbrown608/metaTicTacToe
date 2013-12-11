"""
Computer agent to play metaTicTacToe.
Computer plays by negamax with alpha-beta pruning.
Pseudocode from http://chessprogramming.wikispaces.com/Negamax

Created on Oct 30, 2013
@author: vbrown
"""

import copy
import logging
import re
from Models import User, Game
 
def nextMove(game):
    """
    Compute the next move for a player.
    This is a wrapper function for the recursive function negamax.
    
    We calculate maximum search depth based on the number of empty cells remaining on the metaboard.
    Why?
    1. Search is slow at the beginning because the branching factor is high - so depth should be small (~4).
    2. Deep search is worth more close to the end of the game - so go deep (up to 8)
    
    Arguments: 
        game: Game object to evaluate
        
    Return:
        (board_num, cell): the best move
    """
    cells_remaining = sum(map(lambda s: s.count(' '), game.metaboard))
    max_depth = int(cells_remaining*(-.05) + 8)
    
    util, bestMove = negamax(game, max_depth, float('-inf'), float('inf'))
    return bestMove
 
def negamax(game, depth, alpha, beta):
    """
    Compute the next move for a player given the current board state and also
    compute the utility of that move.
 
    Arguments:
        game: Game object to evaluate
        depth: Maximum search depth
        alpha: best utility for O along path to root - initialize to negative infinity
        beta: best utility for X along path to root - initialize to positive infinity
 
    Return Value:
        utility: The goodness of the move for the Agent (always player O). 
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
        val, move = negamax(tempGame, depth-1, -beta, -alpha)
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
    """
    Returns liklihood that the current board will lead to a win for the current player. 
    
    Arguments:
        game: Game object to evaluate
        
    Return Value:
        utility: Large numbers are good for player X. Small numbers are good for O.
    """
    player_coef = 1 if game.moveX else -1
    if game.winner:
        return 1000*player_coef
    mini_win_chances = 0
    
    # Count the chances for a win on a miniboard (two pieces in a row)
    # TODO: Don't count chances on a miniboards are already won
    for board in game.metaboard:
        mini_win_chances += winChances(board, 'X')
        mini_win_chances -= winChances(board, 'O')
        
    # Count 
    mini_wins = game.all_mini_wins.count('X') - game.all_mini_wins.count('O')
    
    # Count the chances for a win on the metaboard (two miniboards won in a row)
    meta_win_chances = winChances(game.all_mini_wins, 'X') - winChances(game.all_mini_wins, 'O')
    return (mini_win_chances + mini_wins*10 + meta_win_chances*15)*player_coef
    
def winChances(board, player):
    """
    Compute the number of possible wins (two in a row with third cell empty). 
    Used to judge likelihood that current board will lead to a win.
    
    Arguments:
        board: the board to evaluate (list or string)
        player: whose chances are we counting? 'X' or 'O'
        
    Return Value:
        Number of instances where player has two pieces in a row with third position empty.
    
    Note: this is slow. I'd like to speed things up by only evaluating the miniboard with the most 
    recent move. The other counts would be passed as an additional arg in the recursive function.
    """
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
    """
    Return a list of legal moves available to the current player. 
    Useful for iterating over all possible moves in adversarial search.
    
    Arguments:
        game: Game object to evaluate
    
    Return Value: 
        List of legal moves available to the current player. 
        Legal moves are represented as (board, cell)
    """
    if game.winner:
        return []
    
    # Account for a special case where the board to play in is full.
    # In that case, all boards become legal.
    boards = range(9) if game.last_cell == -1 else [game.last_cell] 
    
    result = []
    for board in boards:
        for cell in range(len(game.metaboard[board])):
            if game.metaboard[board][cell] == ' ': result += [(board, cell)]
    return result