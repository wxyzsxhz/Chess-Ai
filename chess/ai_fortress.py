"""
FORTRESS AI PERSONALITY - "The Defensive Wall"

Game Theory Concept: Risk-Averse Utility Function
- Heavily weights king safety and defensive structure
- Values pawns more (defensive shield)
- Prefers solid positions over tactical complications
- Conservative piece values

Difficulty: Easy to implement
Implementation: Modified evaluation weights + king safety bonuses
"""

import random
from ai_personality_base import (
    CHECKMATE, STALEMATE, BASE_PIECE_SCORE, BASE_PIECE_POSITION_SCORES,
    findRandomMoves
)

DEPTH = 4  # Standard depth
nextMove = None

pieceScore = {
    "K": 0,
    "Q": 9,
    "R": 5,
    "B": 3,
    "N": 3,
    "p": 1.3  # Pawns worth 30% more (defensive value)
}

# KING SAFETY TABLE - Rewards king staying in corner/castled position
# Higher scores = safer positions for the king
whiteKingSafety = [
    [3, 4, 2, 1, 1, 2, 4, 3],
    [2, 2, 1, 0, 0, 1, 2, 2],
    [1, 1, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0]
]

blackKingSafety = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 1, 1],
    [2, 2, 1, 0, 0, 1, 2, 2],
    [3, 4, 2, 1, 1, 2, 4, 3] 
]

# Use base position scores for other pieces
piecePositionScores = BASE_PIECE_POSITION_SCORES.copy()

# FORTRESS EVALUATION FUNCTION
def scoreBoard(gs):

    # Check for game-ending positions
    if gs.checkmate:
        if gs.whiteToMove:
            gs.checkmate = False
            return -CHECKMATE  # Black wins
        else:
            gs.checkmate = False
            return CHECKMATE  # White wins
    elif gs.stalemate:
        return STALEMATE

    score = 0
    
    # Determine which color we're playing as
    SET_WHITE_AS_BOT = 1 if gs.whiteToMove else -1
    
    # Evaluate each piece on the board
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            square = gs.board[row][col]
            if square != "--":
                piecePositionScore = 0
                
                # Get position score (piece-square table value)
                if square[1] != "K":
                    if square[1] == "p":
                        piecePositionScore = piecePositionScores[square][row][col]
                    else:
                        piecePositionScore = piecePositionScores[square[1]][row][col]
                
                # KING SAFETY BONUS (Fortress special feature)
                if square[1] == "K":
                    if square[0] == "w":
                        piecePositionScore = whiteKingSafety[row][col]
                    else:
                        piecePositionScore = blackKingSafety[row][col]
                
                # Calculate score based on color
                if square[0] == 'w':
                    score += pieceScore[square[1]] + piecePositionScore * 0.15  # Higher position weight
                elif square[0] == 'b':
                    score -= pieceScore[square[1]] + piecePositionScore * 0.15
    
    return score

# SEARCH ALGORITHM (same as original NegaMax with Alpha-Beta)
def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    global nextMove
    if depth == 0:
        return turnMultiplier * scoreBoard(gs)

    maxScore = -CHECKMATE
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, depth-1, -beta, -alpha, -turnMultiplier)
        
        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
                print(f"Fortress: {move} score {score}")
        
        gs.undoMove()
        
        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            break
    
    return maxScore

# MAIN ENTRY POINT
def findBestMove(gs, validMoves, returnQueue=None):
    global nextMove
    nextMove = None
    random.shuffle(validMoves)
    
    # Determine color we're playing
    SET_WHITE_AS_BOT = 1 if gs.whiteToMove else -1
    
    # Start the search
    findMoveNegaMaxAlphaBeta(gs, validMoves, DEPTH, -CHECKMATE, CHECKMATE, SET_WHITE_AS_BOT)
    
    # Return via queue (for multiprocessing) or directly
    if returnQueue is not None:
        returnQueue.put(nextMove)
    else:
        return nextMove