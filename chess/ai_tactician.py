"""
TACTICIAN AI PERSONALITY - "The Short-term Striker"

Game Theory Concept: High Temporal Discount Rate (Myopic/Present-biased)
- Lower search depth (thinks 3 moves ahead vs 4)
- Heavily weights immediate material gains
- Underweights long-term positional advantages
- Bonus for checks and immediate threats
- Repetition detection - avoids draw loops

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

# Game-level position history - tracks actual board positions
gameHistory = {}

# SAME piece values as base (material-focused)
pieceScore = BASE_PIECE_SCORE.copy()

# Use base position scores
piecePositionScores = BASE_PIECE_POSITION_SCORES.copy()

# CAPTURE MULTIPLIER - Captured pieces worth MORE
CAPTURE_BONUS = 1.5

# ============================================================================
# BOARD KEY FUNCTION
# ============================================================================

def _board_key(gs):
    """Canonical position key including all draw-relevant state."""
    return (
        str(gs.board),
        gs.whiteToMove,
        gs.whiteCastleKingside,
        gs.whiteCastleQueenside,
        gs.blackCastleKingside,
        gs.blackCastleQueenside,
        gs.enpasantPossible,
    )

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
        return -CHECKMATE if gs.whiteToMove else CHECKMATE
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
# SEARCH ALGORITHM with Repetition Detection
# ============================================================================

def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier, search_history=None):
    """
    NegaMax search with alpha-beta pruning and repetition detection.
    Uses Tactician scoreBoard() function for evaluation.
    """
    global nextMove
    
    if search_history is None:
        search_history = {}
    
    # Get board key for repetition detection
    rep_key = _board_key(gs)
    
    # ---- REPETITION DETECTION ----
    game_count = gameHistory.get(rep_key, 0)
    search_count = search_history.get(rep_key, 0)
    total_count = game_count + search_count
    
    if total_count >= 2:
        # This position has been seen twice already - third time is a draw
        # Return 0 to discourage repetition
        return 0
    
    if depth == 0:
        return turnMultiplier * scoreBoard(gs)

    maxScore = -CHECKMATE
    
    # Mark current position as visited in search path
    search_history[rep_key] = search_history.get(rep_key, 0) + 1
    
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, depth-1, -beta, -alpha, -turnMultiplier, search_history)
        
        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
        
        gs.undoMove()
        
        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            break
    
    # Unwind search-path counter
    search_history[rep_key] -= 1
    
    return maxScore

# ============================================================================
# MAIN ENTRY POINT - WITH CAPTURE BONUS AND REPETITION DETECTION
# ============================================================================

def findBestMove(gs, validMoves, returnQueue=None):
    """
    Find the best move using Tactician personality.
    
    TACTICIAN SPECIAL: 
    - Looks only 3 moves ahead (short-term thinking)
    - Overvalues captures by 1.5x
    - Avoids repetition
    
    Args:
        gs: GameState object
        validMoves: List of valid moves
        returnQueue: Queue to return move (for multiprocessing)
    
    Returns:
        Move: The best move found
    """
    global nextMove, gameHistory
    nextMove = None
    random.shuffle(validMoves)
    
    # Record current position in game history
    key = _board_key(gs)
    gameHistory[key] = gameHistory.get(key, 0) + 1
    
    SET_WHITE_AS_BOT = 1 if gs.whiteToMove else -1
    
    # Evaluate ALL moves and apply capture bonus
    move_scores = []
    
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        
        # Check if this move leads to a repeated position
        next_key = _board_key(gs)
        if gameHistory.get(next_key, 0) >= 2:
            # This move would lead to a draw by repetition - penalize it
            score = -1000
            print(f"  ⚠️ Avoiding repetition: {move}")
        else:
            score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, DEPTH-1, -CHECKMATE, CHECKMATE, -SET_WHITE_AS_BOT, search_history={})
            
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
        repetition_marker = "⚠️" if score < -500 else ""
        print(f"  {i+1}. {move} → {score:.2f} {capture_marker} {repetition_marker} {marker}")
    print()
    
    if returnQueue is not None:
        returnQueue.put(nextMove)
    else:
        return nextMove


def notify_undo(gs):
    """Call this when a move is undone so gameHistory stays accurate."""
    key = _board_key(gs)
    if gameHistory.get(key, 0) > 0:
        gameHistory[key] -= 1