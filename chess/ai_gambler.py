"""
🎲 GAMBLER AI - ULTIMATE FAST VERSION ♟️🔥

Depth: 4 (FAST)

ENGINE OPTIMIZATIONS:
✅ Alpha-Beta Pruning
✅ Move Ordering (captures first)
✅ Killer Move Heuristic
✅ Transposition Table Cache
✅ Repetition Detection - prevents draws
✅ Only ONE deep search at root
✅ Gambler randomness among top moves
"""

import random
from ai_personality_base import (
    CHECKMATE,
    STALEMATE,
    BASE_PIECE_POSITION_SCORES
)

# ============================================================================
# CONFIG
# ============================================================================

DEPTH = 4
nextMove = None

# Game-level position history - tracks actual board positions
gameHistory = {}

pieceScore = {
    "K": 0,
    "Q": 9,
    "R": 5,
    "B": 3.3,
    "N": 3.3,
    "p": 1
}

piecePositionScores = BASE_PIECE_POSITION_SCORES.copy()

CENTER_BONUS = 0.08

# ============================================================================
# SPEED BOOSTERS
# ============================================================================

# Transposition Table Cache
transTable = {}

# Killer Moves (one per depth)
killerMoves = [[None, None] for _ in range(DEPTH + 1)]


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
# FAST EVALUATION
# ============================================================================

def aggression_bonus(piece, row, col):
    """Reward center activity (cheap aggression)."""
    if piece[1] in ["N", "B", "R", "Q"]:
        dist = abs(3.5 - row) + abs(3.5 - col)
        return (4 - dist) * CENTER_BONUS
    return 0


def scoreBoard(gs):
    """Fast evaluation: material + position + aggression."""

    if gs.checkmate:
        return -CHECKMATE if gs.whiteToMove else CHECKMATE

    if gs.stalemate:
        return STALEMATE

    score = 0

    for r in range(8):
        for c in range(8):
            sq = gs.board[r][c]
            if sq == "--":
                continue

            pType = sq[1]

            posScore = 0
            if pType != "K":
                if pType == "p":
                    posScore = piecePositionScores[sq][r][c]
                else:
                    posScore = piecePositionScores[pType][r][c]

            aggro = aggression_bonus(sq, r, c)

            value = pieceScore[pType] + posScore * 0.1 + aggro

            if sq[0] == "w":
                score += value
            else:
                score -= value

    return score


# ============================================================================
# MOVE ORDERING (CAPTURE + KILLER)
# ============================================================================

def orderMoves(moves, depth):
    """Captures first, then killer moves."""

    def movePriority(m):
        if m.isCapture:
            return 3
        if killerMoves[depth][0] == m:
            return 2
        if killerMoves[depth][1] == m:
            return 1
        return 0

    return sorted(moves, key=movePriority, reverse=True)


# ============================================================================
# NEGAMAX + ALPHA-BETA + CACHE + KILLER + REPETITION DETECTION
# ============================================================================

def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier, search_history=None):
    global nextMove

    if search_history is None:
        search_history = {}

    # ---- BOARD KEY FOR CACHE AND REPETITION ----
    boardKey = str(gs.board) + str(gs.whiteToMove)
    rep_key = _board_key(gs)

    # ---- REPETITION DETECTION ----
    game_count = gameHistory.get(rep_key, 0)
    search_count = search_history.get(rep_key, 0)
    total_count = game_count + search_count

    if total_count >= 2:
        # This position has been seen twice already - third time is a draw
        # Return 0 to discourage repetition
        return 0

    # ---- TRANSPOSITION TABLE ----
    if boardKey in transTable:
        storedDepth, storedScore = transTable[boardKey]
        if storedDepth >= depth:
            return storedScore

    # ---- LEAF NODE ----
    if depth == 0:
        return turnMultiplier * scoreBoard(gs)

    maxScore = -CHECKMATE

    # ---- ORDER MOVES ----
    validMoves = orderMoves(validMoves, depth)

    # Mark current position as visited in search path
    search_history[rep_key] = search_history.get(rep_key, 0) + 1

    for move in validMoves:

        gs.makeMove(move)
        nextMoves = gs.getValidMoves()

        score = -findMoveNegaMaxAlphaBeta(
            gs,
            nextMoves,
            depth - 1,
            -beta,
            -alpha,
            -turnMultiplier,
            search_history
        )

        gs.undoMove()

        if score > maxScore:
            maxScore = score

            if depth == DEPTH:
                nextMove = move

        # Alpha update
        alpha = max(alpha, maxScore)

        # ---- PRUNING + KILLER MOVE SAVE ----
        if alpha >= beta:

            if not move.isCapture:
                if killerMoves[depth][0] != move:
                    killerMoves[depth][1] = killerMoves[depth][0]
                    killerMoves[depth][0] = move

            break

    # Unwind search-path counter
    search_history[rep_key] -= 1

    # ---- STORE IN CACHE ----
    transTable[boardKey] = (depth, maxScore)

    return maxScore


# ============================================================================
# MAIN GAMBLER MOVE (FAST ROOT ONLY)
# ============================================================================

def findBestMove(gs, validMoves, returnQueue=None):
    """
    Ultimate Fast Gambler with Repetition Detection.
    """
    global nextMove, gameHistory
    nextMove = None

    # Record current position in game history
    key = _board_key(gs)
    gameHistory[key] = gameHistory.get(key, 0) + 1

    # Safety check - if no valid moves, return None
    if not validMoves:
        if returnQueue:
            returnQueue.put(None)
        return None

    turnMultiplier = 1 if gs.whiteToMove else -1

    # Clear cache each move (but keep gameHistory)
    transTable.clear()

    # ---- FULL SEARCH WITH REPETITION DETECTION ----
    try:
        findMoveNegaMaxAlphaBeta(
            gs,
            validMoves,
            DEPTH,
            -CHECKMATE,
            CHECKMATE,
            turnMultiplier,
            search_history={}  # Fresh search path history
        )
    except Exception as e:
        print(f"⚠️ Gambler search error: {e}")
        nextMove = None

    # ✅ SAFETY: If search failed, fallback to random
    if nextMove is None:
        print("⚠️ Gambler fallback: random move")
        finalMove = random.choice(validMoves)

        print("\n🎲 Gambler Final Choice (Fallback):")
        print(f"  1. {finalMove} ✓ CHOSEN (random)")

        if returnQueue:
            returnQueue.put(finalMove)
        return finalMove

    # ---- GAMBLER RANDOMNESS ----
    # Pick from best + random alternatives
    topMoves = [nextMove]

    # Add up to 2 random unique moves
    random.shuffle(validMoves)
    for m in validMoves:
        if m != nextMove and m not in topMoves:
            topMoves.append(m)
        if len(topMoves) >= 3:  # Stop when we have 3 moves
            break

    # Adjust weights based on how many moves we actually have
    move_count = len(topMoves)
    
    if move_count == 1:
        # Only one move available
        weights = [1.0]
    elif move_count == 2:
        # Two moves available
        weights = [0.75, 0.25]
    else:  # move_count >= 3
        # Three or more moves available - use top 3 with standard weights
        weights = [0.65, 0.25, 0.10]
        # If we somehow got more than 3, trim to 3
        if move_count > 3:
            topMoves = topMoves[:3]

    # Choose randomly based on weights
    chosen = random.choices(
        topMoves,
        weights=weights
    )[0]

    print("\n🎲 Gambler Final Choice:")
    for i, m in enumerate(topMoves[:3]):  # Only show up to 3
        mark = "✓ CHOSEN" if m == chosen else ""
        print(f"  {i+1}. {m} {mark}")

    if returnQueue:
        returnQueue.put(chosen)

    return chosen


def notify_undo(gs):
    """Call this when a move is undone so gameHistory stays accurate."""
    key = _board_key(gs)
    if gameHistory.get(key, 0) > 0:
        gameHistory[key] -= 1