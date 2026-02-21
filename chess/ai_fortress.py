"""
FORTRESS AI PERSONALITY - "The Defensive Wall" (WITH CACHING)

Game Theory Concept: Risk-Averse Utility Function
- Heavily weights king safety and defensive structure
- Values pawns more (defensive shield)
- Prefers solid positions over tactical complications
- Conservative piece values

Difficulty: Easy to implement
Implementation: Modified evaluation weights + king safety bonuses
ENGINE OPTIMIZATIONS: Iterative Deepening + Quiescence
"""

import time
from ai_personality_base import (
    CHECKMATE, STALEMATE, BASE_PIECE_SCORE, BASE_PIECE_POSITION_SCORES,
    findRandomMoves, TranspositionTable, get_position_hash, order_moves
)

DEPTH = 4
TIME_LIMIT = 2.0 
nextMove = None

tt = TranspositionTable()

pieceScore = {
    "K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "p": 1.3
}

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

piecePositionScores = BASE_PIECE_POSITION_SCORES.copy()

# EVALUATION
def scoreBoard(gs):
    if gs.checkmate:
        if gs.whiteToMove:
            gs.checkmate = False
            return -CHECKMATE
        else:
            gs.checkmate = False
            return CHECKMATE
    elif gs.stalemate:
        return STALEMATE

    score = 0
    
    for row in range(8):
        for col in range(8):
            square = gs.board[row][col]
            if square != "--":
                piecePositionScore = 0
                
                if square[1] != "K":
                    if square[1] == "p":
                        piecePositionScore = piecePositionScores[square][row][col]
                    else:
                        piecePositionScore = piecePositionScores[square[1]][row][col]
                else:
                    if square[0] == "w":
                        piecePositionScore = whiteKingSafety[row][col]
                    else:
                        piecePositionScore = blackKingSafety[row][col]
                
                if square[0] == 'w':
                    score += pieceScore[square[1]] + piecePositionScore * 0.15
                elif square[0] == 'b':
                    score -= pieceScore[square[1]] + piecePositionScore * 0.15
    
    return score

# QUIESCENCE SEARCH (prevents horizon effect)
def quiescence(gs, alpha, beta, turnMultiplier):
    """
    Only search captures and checks at leaf nodes.
    Prevents evaluation of unstable positions.
    """
    stand_pat = turnMultiplier * scoreBoard(gs)
    
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat
    
    # Only look at captures
    moves = gs.getValidMoves()
    captures = [m for m in moves if m.pieceCaptured != '--']
    
    for move in captures:
        gs.makeMove(move)
        score = -quiescence(gs, -beta, -alpha, -turnMultiplier)
        gs.undoMove()
        
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    
    return alpha

# SEARCH WITH QUIESCENCE
def negamax(gs, depth, alpha, beta, turnMultiplier, start_time):
    global nextMove
    
    # Time cutoff
    if time.time() - start_time > TIME_LIMIT:
        return 0
    
    # Leaf node - use quiescence
    if depth == 0:
        return quiescence(gs, alpha, beta, turnMultiplier)
    
    # Check cache
    pos_hash = get_position_hash(gs)
    cached = tt.get(pos_hash, depth)
    if cached is not None:
        return cached
    
    # Generate and order moves
    moves = gs.getValidMoves()
    ordered_moves = order_moves(moves, pieceScore)
    
    maxScore = -CHECKMATE
    for move in ordered_moves:
        gs.makeMove(move)
        score = -negamax(gs, depth-1, -beta, -alpha, -turnMultiplier, start_time)
        gs.undoMove()
        
        if score > maxScore:
            maxScore = score
        
        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            break
    
    # Cache result
    tt.store(pos_hash, depth, maxScore)
    
    return maxScore

# ITERATIVE DEEPENING
def findBestMove(gs, validMoves, returnQueue=None):
    global nextMove
    nextMove = None
    
    start_time = time.time()
    best_move = validMoves[0] if validMoves else None
    
    SET_WHITE_AS_BOT = 1 if gs.whiteToMove else -1
    
    # Iterative deepening: depth 1 → 2 → 3 → 4
    for depth in range(1, DEPTH + 1):
        if time.time() - start_time > TIME_LIMIT:
            break
        
        ordered_moves = order_moves(validMoves, pieceScore)
        best_score = -CHECKMATE
        
        for move in ordered_moves:
            gs.makeMove(move)
            score = -negamax(gs, depth-1, -CHECKMATE, CHECKMATE, -SET_WHITE_AS_BOT, start_time)
            gs.undoMove()
            
            if time.time() - start_time > TIME_LIMIT:
                break
            
            if score > best_score:
                best_score = score
                best_move = move
        
        nextMove = best_move
        print(f"🏰 Fortress depth {depth}: {nextMove} → {best_score:.2f}")
    
    elapsed = time.time() - start_time
    print(f"🏰 Final choice: {nextMove} ({elapsed:.2f}s)")
    
    if returnQueue is not None:
        returnQueue.put(nextMove)
    else:
        return nextMove