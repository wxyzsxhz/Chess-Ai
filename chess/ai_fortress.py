"""
FORTRESS AI PERSONALITY - "The Defender"

Game Theory Concept: Risk-Averse Utility Function / Maximin Strategy
- Maximizes minimum guaranteed outcome rather than expected outcome
- Genuinely defensive behavior enforced at THREE levels:
    1. scoreBoard()     — rewards safe positions, penalizes exposure
    2. score_with_risk_penalty() — applies variance penalty to root moves
                                   (risk-averse utility function)
    3. _root_search()   — prefers consolidating trades when ahead,
                          penalizes advancing pieces deep into enemy territory

Difficulty: Easy
"""

import random
import time
from ai_personality_base import (
    CHECKMATE, STALEMATE, BASE_PIECE_SCORE, BASE_PIECE_POSITION_SCORES,
    findRandomMoves
)

# ============================================================================
# CONFIGURATION
# ============================================================================

DEPTH = 3
nextMove = None

pieceScore = {
    "K": 0,
    "Q": 9,
    "R": 5,
    "B": 3,
    "N": 3,
    "p": 1.4   # Fortress values pawns more — they form the defensive wall
}

piecePositionScores = BASE_PIECE_POSITION_SCORES.copy()

# ============================================================================
# RISK-AVERSE PARAMETERS
# ============================================================================

AGGRESSION_PENALTY    = 0.4
VARIANCE_PENALTY      = 0.3
TRADE_THRESHOLD       = 1.0
TRADE_BONUS           = 0.25
OVEREXTENSION_PENALTY = 0.3

# ============================================================================
# EVALUATION
# ============================================================================

def scoreBoard(gs):
    if gs.checkmate:
        return -CHECKMATE if gs.whiteToMove else CHECKMATE
    elif gs.stalemate:
        return STALEMATE

    score = 0
    white_king_row, white_king_col = 7, 4
    black_king_row, black_king_col = 0, 4
    white_pawn_cols = []
    black_pawn_cols = []

    for row in range(8):
        for col in range(8):
            sq = gs.board[row][col]
            if sq == "--":
                continue
            color, piece = sq[0], sq[1]
            mat = pieceScore[piece]
            pos = 0
            if piece != "K":
                pos = piecePositionScores[sq if piece == "p" else piece][row][col]
            total = mat + pos * 0.1

            if color == "w":
                score += total
                if piece == "K": white_king_row, white_king_col = row, col
                if piece == "p": white_pawn_cols.append(col)
            else:
                score -= total
                if piece == "K": black_king_row, black_king_col = row, col
                if piece == "p": black_pawn_cols.append(col)

    def king_safety(king_row, king_col, color):
        safety = 0
        if king_col <= 2:    safety += 0.6
        elif king_col >= 5:  safety += 0.7
        else:                safety -= 0.8
        shield_row = king_row - 1 if color == "w" else king_row + 1
        if 0 <= shield_row < 8:
            for c in range(max(0, king_col - 1), min(8, king_col + 2)):
                pawn_sq = gs.board[shield_row][c]
                if pawn_sq == color + "p":  safety += 0.4
                elif pawn_sq == "--":       safety -= 0.25
        shield_row2 = king_row - 2 if color == "w" else king_row + 2
        if 0 <= shield_row2 < 8:
            for c in range(max(0, king_col - 1), min(8, king_col + 2)):
                if gs.board[shield_row2][c] == color + "p":
                    safety += 0.15
        return safety

    score += king_safety(white_king_row, white_king_col, "w")
    score -= king_safety(black_king_row, black_king_col, "b")

    def pawn_structure(pawn_cols):
        if not pawn_cols:
            return 0
        s = 0
        col_set = set(pawn_cols)
        for c in pawn_cols:
            if (c - 1) in col_set or (c + 1) in col_set:
                s += 0.1
            else:
                s -= 0.2
        return s

    score += pawn_structure(white_pawn_cols)
    score -= pawn_structure(black_pawn_cols)

    return score


def is_overextending(move, color):
    if move.pieceMoved[1] not in ("Q", "R"):
        return False
    if move.pieceCaptured != "--":
        return False
    if color == "w":
        return move.endRow <= 2
    else:
        return move.endRow >= 5


def material_balance(gs, color):
    score = 0
    for row in range(8):
        for col in range(8):
            sq = gs.board[row][col]
            if sq == "--": continue
            val = pieceScore.get(sq[1], 0)
            if sq[0] == color:
                score += val
            else:
                score -= val
    return score


# ============================================================================
# MOVE ORDERING
# ============================================================================

def order_moves(moves):
    winning, equal, quiet, losing = [], [], [], []
    for move in moves:
        if move.pieceCaptured != "--":
            gain = (pieceScore.get(move.pieceCaptured[1], 0)
                    - pieceScore.get(move.pieceMoved[1], 0))
            if gain > 0:    winning.append(move)
            elif gain == 0: equal.append(move)
            else:           losing.append(move)
        else:
            quiet.append(move)
    return winning + equal + quiet + losing


# ============================================================================
# INNER NEGAMAX
# ============================================================================

def _negamax(gs, moves, depth, alpha, beta, turnMultiplier, tt):
    board_key = (str(gs.board), gs.whiteToMove)

    if board_key in tt:
        tt_depth, tt_score, tt_flag = tt[board_key]
        if tt_depth >= depth:
            if   tt_flag == "exact": return tt_score
            elif tt_flag == "lower": alpha = max(alpha, tt_score)
            elif tt_flag == "upper": beta  = min(beta,  tt_score)
            if alpha >= beta:        return tt_score

    if depth == 0:
        result = turnMultiplier * scoreBoard(gs)
        tt[board_key] = (0, result, "exact")
        return result

    if depth >= 2:
        moves = order_moves(moves)

    maxScore   = -CHECKMATE
    orig_alpha = alpha

    for move in moves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -_negamax(gs, nextMoves, depth - 1, -beta, -alpha,
                          -turnMultiplier, tt)
        gs.undoMove()

        if score > maxScore:
            maxScore = score
        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            break

    if maxScore <= orig_alpha:   flag = "upper"
    elif maxScore >= beta:       flag = "lower"
    else:                        flag = "exact"
    tt[board_key] = (depth, maxScore, flag)
    return maxScore


# ============================================================================
# ROOT SEARCH
# ============================================================================

def _root_search(gs, validMoves, depth, turnMultiplier, color):
    tt = {}
    ordered = order_moves(validMoves)
    mat_advantage = material_balance(gs, color)

    raw_scores     = {}
    shallow_scores = {}

    for move in ordered:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        s1 = -_negamax(gs, nextMoves, 0, -CHECKMATE, CHECKMATE,
                       -turnMultiplier, tt)
        gs.undoMove()
        shallow_scores[id(move)] = s1

    alpha = -CHECKMATE
    for move in ordered:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -_negamax(gs, nextMoves, depth - 1,
                          -CHECKMATE, -alpha, -turnMultiplier, tt)
        gs.undoMove()
        raw_scores[id(move)] = score
        if score > alpha:
            alpha = score

    adjusted = []
    for move in ordered:
        raw = raw_scores[id(move)]
        s1  = shallow_scores[id(move)]
        adj = raw

        adj -= VARIANCE_PENALTY * abs(raw - s1)

        if is_overextending(move, color):
            adj -= OVEREXTENSION_PENALTY

        if mat_advantage > TRADE_THRESHOLD and move.pieceCaptured != "--":
            cap_val = pieceScore.get(move.pieceCaptured[1], 0)
            mov_val = pieceScore.get(move.pieceMoved[1], 0)
            if cap_val >= mov_val:
                adj += TRADE_BONUS

        adjusted.append((move, raw, adj))

    adjusted.sort(key=lambda x: x[2], reverse=True)
    bestMove = adjusted[0][0]
    display  = [(mv, adj) for mv, raw, adj in adjusted]
    return bestMove, display


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def findBestMove(gs, validMoves, returnQueue=None):
    global nextMove
    nextMove = None
    random.shuffle(validMoves)

    color = "w" if gs.whiteToMove else "b"
    side  = "White" if gs.whiteToMove else "Black"
    turn  = 1 if gs.whiteToMove else -1

    start = time.time()
    chosen, display_scores = _root_search(gs, validMoves, DEPTH, turn, color)
    elapsed = time.time() - start

    board_eval = scoreBoard(gs)
    mat_adv    = material_balance(gs, color)
    adv        = "White" if board_eval >= 0 else "Black"

    print(f"\n🏰 FORTRESS ({side}) | depth {DEPTH}")
    print(f"  {'Rnk':<4} {'Move':<14} {'Score':>7}  Notes")
    print(f"  {'─'*42}")
    for i, (mv, sc) in enumerate(display_scores[:5]):
        tags = []
        if mv == chosen:                tags.append("✅")
        if mv.pieceCaptured != "--":    tags.append("⚔")
        if is_overextending(mv, color): tags.append("⚠overext")
        print(f"  {i+1:<4} {str(mv):<14} {sc:>7.2f}  {' '.join(tags)}")
    print(f"  {'─'*42}")
    print(f"  ✅ {chosen}  |  eval {board_eval:+.2f} ({adv})  |  mat {mat_adv:+.1f}  |  {elapsed:.2f}s\n")

    nextMove = chosen

    if returnQueue is not None:
        returnQueue.put(chosen)
    else:
        return chosen