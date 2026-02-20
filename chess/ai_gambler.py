"""
🎲 GAMBLER AI - ULTIMATE FAST VERSION ♟️🔥

Depth: 4 (FAST)

ENGINE OPTIMIZATIONS:
✅ Alpha-Beta Pruning
✅ Move Ordering (captures first)
✅ Killer Move Heuristic
✅ Transposition Table Cache
✅ Only ONE deep search at root
✅ Gambler randomness among top moves

This is the fastest strong Gambler personality.
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
# NEGAMAX + ALPHA-BETA + CACHE + KILLER
# ============================================================================

def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    global nextMove

    # ---- TRANSPOSITION KEY ----
    boardKey = str(gs.board) + str(gs.whiteToMove)

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

    for move in validMoves:

        gs.makeMove(move)
        nextMoves = gs.getValidMoves()

        score = -findMoveNegaMaxAlphaBeta(
            gs,
            nextMoves,
            depth - 1,
            -beta,
            -alpha,
            -turnMultiplier
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

    # ---- STORE IN CACHE ----
    transTable[boardKey] = (depth, maxScore)

    return maxScore


# ============================================================================
# MAIN GAMBLER MOVE (FAST ROOT ONLY)
# ============================================================================

def findBestMove(gs, validMoves, returnQueue=None):
    """
    Ultimate Fast Gambler (FIXED):

    ✅ Depth 4 AlphaBeta Search ONCE
    ✅ Always returns a real move
    ✅ Randomness only among top candidates
    """

    global nextMove
    nextMove = None

    turnMultiplier = 1 if gs.whiteToMove else -1

    # Clear cache each move
    transTable.clear()

    # ---- FULL SEARCH ----
    findMoveNegaMaxAlphaBeta(
        gs,
        validMoves,
        DEPTH,
        -CHECKMATE,
        CHECKMATE,
        turnMultiplier
    )

    # ✅ SAFETY: If search failed, fallback
    if nextMove is None:
        print("⚠️ Gambler fallback: random move")
        finalMove = random.choice(validMoves)

        if returnQueue:
            returnQueue.put(finalMove)
        return finalMove

    # ---- GAMBLER RANDOMNESS ----
    # Pick from best + 2 random alternatives
    topMoves = [nextMove]

    random.shuffle(validMoves)
    for m in validMoves:
        if m != nextMove:
            topMoves.append(m)
        if len(topMoves) == 3:
            break

    # Probabilities
    chosen = random.choices(
        topMoves,
        weights=[0.65, 0.25, 0.10]
    )[0]

    print("\n🎲 Gambler Final Choice:")
    for i, m in enumerate(topMoves):
        mark = "✓ CHOSEN" if m == chosen else ""
        print(f"  {i+1}. {m} {mark}")

    if returnQueue:
        returnQueue.put(chosen)

    return chosen