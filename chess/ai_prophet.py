"""
PROPHET AI PERSONALITY - "The Grandmaster" (WITH CACHING)

Game Theory Concept: Low Temporal Discount Rate (Long-term thinking)
- Looks deeper into the game tree (higher DEPTH)
- Values positional advantages heavily
- Thinks 5 moves ahead vs 4
- Optimized for better performance

Difficulty: Hard (performance concerns with depth=5)
Implementation: Increased DEPTH + higher positional weight + move ordering
ENGINE OPTIMIZATIONS: Iterative Deepening + Quiescence
"""

import random
import time
from ai_personality_base import (
    CHECKMATE, STALEMATE, BASE_PIECE_SCORE, BASE_PIECE_POSITION_SCORES,
    findRandomMoves, TranspositionTable, get_position_hash, order_moves
)

DEPTH = 5
TIME_LIMIT = 3.0
nextMove = None

tt = TranspositionTable()

pieceScore = BASE_PIECE_SCORE.copy()
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
                
                # Prophet: 3x position weight
                if square[0] == 'w':
                    score += pieceScore[square[1]] + piecePositionScore * 0.3
                elif square[0] == 'b':
                    score -= pieceScore[square[1]] + piecePositionScore * 0.3
    
    return score

# QUIESCENCE SEARCH
def quiescence(gs, alpha, beta, turnMultiplier):
    stand_pat = turnMultiplier * scoreBoard(gs)
    
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat
    
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

# SEARCH
def negamax(gs, depth, alpha, beta, turnMultiplier, start_time):
    if time.time() - start_time > TIME_LIMIT:
        return 0
    
    if depth == 0:
        return quiescence(gs, alpha, beta, turnMultiplier)
    
    pos_hash = get_position_hash(gs)
    cached = tt.get(pos_hash, depth)
    if cached is not None:
        return cached
    
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
    
    tt.store(pos_hash, depth, maxScore)
    return maxScore

# ITERATIVE DEEPENING
def findBestMove(gs, validMoves, returnQueue=None):
    global nextMove
    nextMove = None
    
    start_time = time.time()
    best_move = validMoves[0] if validMoves else None
    
    SET_WHITE_AS_BOT = 1 if gs.whiteToMove else -1
    
    # Iterative deepening: 1 → 2 → 3 → 4 → 5
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
        print(f"🔮 Prophet depth {depth}: {nextMove} → {best_score:.2f}")
    
    elapsed = time.time() - start_time
    print(f"🔮 Final choice: {nextMove} ({elapsed:.2f}s)")
    
    if returnQueue is not None:
        returnQueue.put(nextMove)
    else:
        return nextMove