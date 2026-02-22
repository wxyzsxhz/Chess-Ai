"""
TACTICIAN AI PERSONALITY - "The Short-term Striker"

Game Theory Concept: High Temporal Discount Rate (Myopic/Present-biased)
- Lower search depth (thinks 3 moves ahead vs 4)
- Heavily weights immediate material gains
- Underweights long-term positional advantages
- Bonus for checks and immediate threats

Difficulty: Medium
Implementation: Reduced depth + modified evaluation weights
"""

import random
from ai_personality_base import (
    CHECKMATE, STALEMATE, BASE_PIECE_SCORE, BASE_PIECE_POSITION_SCORES,
    findRandomMoves
)

# ============================================================================
# TACTICIAN CONFIGURATION
# ============================================================================

DEPTH = 3  # LOWER DEPTH - Only looks 3 moves ahead (short-term focus!)
nextMove = None

# SAME piece values as base (material-focused)
pieceScore = BASE_PIECE_SCORE.copy()

# Use base position scores
piecePositionScores = BASE_PIECE_POSITION_SCORES.copy()

# CAPTURE MULTIPLIER - Captured pieces worth MORE
CAPTURE_BONUS = 1.5

# ============================================================================
# HELPER FUNCTION - Check if King is in Check
# ============================================================================

def is_giving_check(gs):
    """
    Check if the current position has the opponent king in check.
    
    Returns:
        bool: True if opponent is in check
    """
    # The opponent is in check if gs.inCheck is True
    # (because we just made a move, so it's now opponent's turn)
    return gs.inCheck

# ============================================================================
# TACTICIAN EVALUATION FUNCTION
# ============================================================================

def scoreBoard(gs):
    """
    Evaluate board position from Tactician perspective.
    
    Key differences from base AI:
    1. LOWER position weight (0.05 vs 0.1) - doesn't care about placement
    2. Will add capture bonus in findBestMove (not here)
    3. Bonus for giving check
    
    Returns:
        int: Position score (positive = good for white, negative = good for black)
    """
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
    
    # Bonus for giving check (immediate pressure!)
    check_bonus = 0
    if is_giving_check(gs):
        check_bonus = 0.5  # Small bonus for checks
    
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
                # NOTE: Position weight is 0.05 (HALF of normal 0.1)
                # This means Tactician cares LESS about where pieces are
                if square[0] == 'w':
                    score += pieceScore[square[1]] + piecePositionScore * 0.05
                elif square[0] == 'b':
                    score -= pieceScore[square[1]] + piecePositionScore * 0.05
    
    # Add check bonus for the side that just moved
    if not gs.whiteToMove:  # Black just moved
        score -= check_bonus
    else:  # White just moved
        score += check_bonus
    
    return score

# ============================================================================
# SEARCH ALGORITHM (same as original NegaMax with Alpha-Beta)
# ============================================================================

def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    """
    NegaMax search with alpha-beta pruning.
    Uses Tactician scoreBoard() function for evaluation.
    """
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
        
        gs.undoMove()
        
        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            break
    
    return maxScore

# ============================================================================
# MAIN ENTRY POINT - WITH CAPTURE BONUS
# ============================================================================

def findBestMove(gs, validMoves, returnQueue=None):
    """
    Find the best move using Tactician personality.
    
    TACTICIAN SPECIAL: 
    - Looks only 3 moves ahead (short-term thinking)
    - Overvalues captures by 1.5x
    
    Args:
        gs: GameState object
        validMoves: List of valid moves
        returnQueue: Queue to return move (for multiprocessing)
    
    Returns:
        Move: The best move found
    """
    global nextMove
    nextMove = None
    random.shuffle(validMoves)
    
    SET_WHITE_AS_BOT = 1 if gs.whiteToMove else -1
    
    # Evaluate ALL moves and apply capture bonus
    move_scores = []
    
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, DEPTH-1, -CHECKMATE, CHECKMATE, -SET_WHITE_AS_BOT)
        
        # TACTICIAN SPECIAL: Bonus for captures!
        if move.pieceCaptured != '--':
            captured_value = pieceScore[move.pieceCaptured[1]]
            capture_bonus = captured_value * (CAPTURE_BONUS - 1.0)  # Extra 0.5x value
            score += capture_bonus
            print(f"  💥 Capture bonus for {move}: +{capture_bonus:.2f}")
        
        move_scores.append((move, score))
        gs.undoMove()
    
    # Sort by score and pick the best
    move_scores.sort(key=lambda x: x[1], reverse=True)
    nextMove = move_scores[0][0]
    best_score = move_scores[0][1]
    
    # Print top 3 options
    print(f"\n⚔️ Tactician's Analysis (Depth {DEPTH}):")
    for i, (move, score) in enumerate(move_scores[:3]):
        marker = "✓ CHOSEN" if i == 0 else ""
        capture_marker = "💥" if move.pieceCaptured != '--' else ""
        print(f"  {i+1}. {move} → {score:.2f} {capture_marker} {marker}")
    print()
    
    if returnQueue is not None:
        returnQueue.put(nextMove)
    else:
        return nextMove