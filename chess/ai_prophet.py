"""
PROPHET AI PERSONALITY - "The Grandmaster"

Game Theory Concept: Low Temporal Discount Rate (Long-term thinking)
- Looks deeper into the game tree (higher DEPTH)
- Values positional advantages heavily
- Thinks 5-6 moves ahead vs 4
- Less concerned with immediate material, more with long-term position

Difficulty: Hard (performance concerns with depth=5)
Implementation: Increased DEPTH + higher positional weight
"""

import random
from ai_personality_base import (
    CHECKMATE, STALEMATE, BASE_PIECE_SCORE, BASE_PIECE_POSITION_SCORES,
    findRandomMoves
)

DEPTH = 5 
nextMove = None

# Same piece values as standard (material is standard)
pieceScore = BASE_PIECE_SCORE.copy()

# Use base position scores
piecePositionScores = BASE_PIECE_POSITION_SCORES.copy()

# PROPHET EVALUATION FUNCTION
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
                
                # Calculate score based on color
                # Prophet values piece placement 3x more than base AI
                if square[0] == 'w':
                    score += pieceScore[square[1]] + piecePositionScore * 0.3  # TRIPLED weight!
                elif square[0] == 'b':
                    score -= pieceScore[square[1]] + piecePositionScore * 0.3
    
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
                print(f"Prophet: {move} score {score}")
        
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
    
    SET_WHITE_AS_BOT = 1 if gs.whiteToMove else -1
    
    # Start the search with DEPTH=5
    findMoveNegaMaxAlphaBeta(gs, validMoves, DEPTH, -CHECKMATE, CHECKMATE, SET_WHITE_AS_BOT)
    
    if returnQueue is not None:
        returnQueue.put(nextMove)
    else:
        return nextMove