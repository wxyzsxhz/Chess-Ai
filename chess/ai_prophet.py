"""
PROPHET AI PERSONALITY - "The Grandmaster"

Game Theory Concept: Low Temporal Discount Rate (Long-term thinking / Backward Induction)
- Searches deepest of all AIs via time-limited iterative deepening
- Heavily weights positional advantages over immediate material
- Evaluates pawn structure, passed pawns, piece coordination

Speed optimizations:
  1. Persistent transposition table — survives across moves
  2. Aspiration windows with same-parity comparison (fixes odd-even effect)
  3. Immediate full-window fallback when checkmate score detected (fixes ×10 widenings)
  4. Time limit — depth 5 only if time budget allows
  5. MVV-LVA capture ordering + killer moves + history heuristic

Fixes applied:
  6. Repetition detection — penalizes revisiting positions (prevents draw-by-repetition bug)
  7. Compact terminal output
"""

import random
import time
from ai_personality_base import (
    CHECKMATE, STALEMATE, BASE_PIECE_SCORE, BASE_PIECE_POSITION_SCORES,
)

# ============================================================================
# CONFIGURATION
# ============================================================================

DEPTH      = 5
TIME_LIMIT = 8.0

nextMove = None

pieceScore          = BASE_PIECE_SCORE.copy()
piecePositionScores = BASE_PIECE_POSITION_SCORES.copy()

# Persistent TT — intentionally never cleared between moves
transTable   = {}
killerMoves  = [[None, None] for _ in range(DEPTH + 2)]
historyTable = {}

# Game-level position history — tracks how many times each position
# has occurred on the actual board (not inside the search tree).
# Passed into negamax so it can detect and penalize repetition.
gameHistory = {}

ASPIRATION_DELTA_INITIAL = 1.5
ASPIRATION_DELTA_TIGHT   = 0.75
CHECKMATE_THRESHOLD      = CHECKMATE * 0.9   # 900


# ============================================================================
# EVALUATION
# ============================================================================

def scoreBoard(gs):
    if gs.checkmate:
        return -CHECKMATE if gs.whiteToMove else CHECKMATE
    elif gs.stalemate:
        return STALEMATE

    score = 0
    white_bishops = 0
    black_bishops = 0
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
            total = mat + pos * 0.3

            if color == "w":
                score += total
                if piece == "B": white_bishops += 1
                if piece == "K": white_king_row, white_king_col = row, col
                if piece == "p": white_pawn_cols.append(col)
            else:
                score -= total
                if piece == "B": black_bishops += 1
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
                if pawn_sq == color + "p": safety += 0.4
                elif pawn_sq == "--":      safety -= 0.25
        return safety

    score += king_safety(white_king_row, white_king_col, "w")
    score -= king_safety(black_king_row, black_king_col, "b")

    if white_bishops >= 2: score += 0.5
    if black_bishops >= 2: score -= 0.5

    for col in range(8):
        for row in range(8):
            sq = gs.board[row][col]
            if sq == "wp":
                if all(gs.board[r][c] != "bp"
                       for c in range(max(0, col-1), min(8, col+2))
                       for r in range(0, row)):
                    score += (7 - row) * 0.15
            elif sq == "bp":
                if all(gs.board[r][c] != "wp"
                       for c in range(max(0, col-1), min(8, col+2))
                       for r in range(row+1, 8)):
                    score -= row * 0.15

    w_cols = set(white_pawn_cols)
    b_cols = set(black_pawn_cols)
    for col in range(8):
        for row in range(8):
            sq = gs.board[row][col]
            if sq == "wR":
                if col not in w_cols and col not in b_cols: score += 0.3
                elif col not in w_cols:                     score += 0.15
            elif sq == "bR":
                if col not in b_cols and col not in w_cols: score -= 0.3
                elif col not in b_cols:                     score -= 0.15

    return score


# ============================================================================
# MOVE ORDERING
# ============================================================================

CENTER = {(3, 3), (3, 4), (4, 3), (4, 4)}

def mvv_lva(move):
    victim   = pieceScore.get(move.pieceCaptured[1], 0)
    attacker = pieceScore.get(move.pieceMoved[1], 1)
    return victim * 10 - attacker

def order_moves(moves, depth, best_move=None):
    best_bucket, win_cap, eq_cap, lose_cap = [], [], [], []
    killer_bucket, history_bucket, center_bucket, other = [], [], [], []

    k1 = killerMoves[depth][0]
    k2 = killerMoves[depth][1]

    for move in moves:
        if best_move and move == best_move:
            best_bucket.append(move)
            continue
        if move.pieceCaptured != "--":
            gain = mvv_lva(move)
            if gain > 0:    win_cap.append((gain, move))
            elif gain == 0: eq_cap.append(move)
            else:           lose_cap.append(move)
        else:
            if move == k1 or move == k2:
                killer_bucket.append(move)
            elif (move.pieceMoved, move.endRow, move.endCol) in historyTable:
                history_bucket.append(move)
            elif (move.endRow, move.endCol) in CENTER:
                center_bucket.append(move)
            else:
                other.append(move)

    win_cap.sort(key=lambda x: x[0], reverse=True)
    return (best_bucket
            + [m for _, m in win_cap]
            + eq_cap
            + killer_bucket
            + history_bucket
            + center_bucket
            + other
            + lose_cap)


# ============================================================================
# QUIESCENCE SEARCH
# ============================================================================

def quiescence(gs, alpha, beta, turn, deadline):
    """
    Extends search through captures until the position is 'quiet'.

    Without quiescence, Prophet evaluates positions mid-sequence —
    e.g. after a queen captures a pawn but before the recapture.
    Quiescence resolves all captures first so the static eval is trustworthy.

    Game Theory note: implements backward induction more faithfully —
    Prophet reasons to a genuinely stable leaf state rather than cutting
    off arbitrarily mid-tactic.
    """
    if time.time() > deadline:
        raise TimeUp

    stand_pat = turn * scoreBoard(gs)

    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    all_moves = gs.getValidMoves()
    captures  = [m for m in all_moves if m.pieceCaptured != "--"]
    captures.sort(key=lambda m: mvv_lva(m), reverse=True)

    for move in captures:
        gs.makeMove(move)
        score = -quiescence(gs, -beta, -alpha, -turn, deadline)
        gs.undoMove()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


# ============================================================================
# NEGAMAX CORE
# ============================================================================

class TimeUp(Exception):
    pass

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

def negamax(gs, moves, depth, alpha, beta, turn, deadline,
            best_move=None, search_history=None):
    """
    search_history: dict mapping board_key → occurrence count
                    within the current search path (not the TT).
                    Used for repetition detection inside the tree.
    """
    if time.time() > deadline:
        raise TimeUp

    if search_history is None:
        search_history = {}

    key = _board_key(gs)

    # ---- Repetition detection ----
    # Count occurrences: game history + search-path history
    game_count   = gameHistory.get(key, 0)
    search_count = search_history.get(key, 0)
    total_count  = game_count + search_count

    if total_count >= 2:
        # This position has been seen twice already — a third visit is a draw.
        # Return 0 (draw score) to discourage repetition.
        return 0

    # ---- Transposition table ----
    if key in transTable:
        tt_d, tt_s, tt_f = transTable[key]
        if tt_d >= depth:
            if   tt_f == "exact": return tt_s
            elif tt_f == "lower": alpha = max(alpha, tt_s)
            elif tt_f == "upper": beta  = min(beta,  tt_s)
            if alpha >= beta:     return tt_s

    if depth == 0:
        return quiescence(gs, alpha, beta, turn, deadline)

    ordered  = order_moves(moves, depth, best_move)
    maxScore = -CHECKMATE
    orig_alpha = alpha

    # Mark this position as visited on the current search path
    search_history[key] = search_history.get(key, 0) + 1

    for move in ordered:
        gs.makeMove(move)
        next_moves = gs.getValidMoves()
        score = -negamax(gs, next_moves, depth - 1, -beta, -alpha, -turn,
                         deadline, search_history=search_history)
        gs.undoMove()

        if score > maxScore:
            maxScore = score
        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            if move.pieceCaptured == "--":
                if killerMoves[depth][0] != move:
                    killerMoves[depth][1] = killerMoves[depth][0]
                    killerMoves[depth][0] = move
                hkey = (move.pieceMoved, move.endRow, move.endCol)
                historyTable[hkey] = historyTable.get(hkey, 0) + depth * depth
            break

    # Unwind search-path counter
    search_history[key] -= 1

    flag = ("upper" if maxScore <= orig_alpha
            else "lower" if maxScore >= beta
            else "exact")
    transTable[key] = (depth, maxScore, flag)
    return maxScore


# ============================================================================
# ITERATIVE DEEPENING WITH ASPIRATION WINDOWS
# ============================================================================

def findMoveIterativeDeepening(gs, validMoves):
    global killerMoves, historyTable

    side = "White" if gs.whiteToMove else "Black"
    print(f"\n🔮 PROPHET ({side}) | {TIME_LIMIT:.0f}s limit")
    print(f"  {'D':<4} {'Move':<14} {'Score':>7}  {'Time':>6}  Note")
    print(f"  {'─'*48}")

    killerMoves  = [[None, None] for _ in range(DEPTH + 2)]
    historyTable = {}

    best_move_so_far = None
    total_start      = time.time()
    deadline         = total_start + TIME_LIMIT
    parity_scores    = [None, None]
    stable_depths    = 0

    for d in range(1, DEPTH + 1):

        elapsed = time.time() - total_start
        if d > 1 and elapsed > TIME_LIMIT * 0.72:
            print(f"  {'─'*48}")
            print(f"  budget exhausted at depth {d}")
            break

        iter_start = time.time()
        note       = ""
        parity     = d % 2
        prev_score = parity_scores[parity]

        if prev_score is None or d <= 2:
            alpha, beta = -CHECKMATE, CHECKMATE
            use_window  = False
        elif abs(prev_score) >= CHECKMATE_THRESHOLD:
            alpha, beta = -CHECKMATE, CHECKMATE
            use_window  = False
            note        = "mate-win"
        else:
            delta      = ASPIRATION_DELTA_TIGHT if stable_depths >= 2 else ASPIRATION_DELTA_INITIAL
            alpha      = prev_score - delta
            beta       = prev_score + delta
            use_window = True

        turn       = 1 if gs.whiteToMove else -1
        iter_best  = None
        root_score = None

        try:
            widening = 0
            while True:
                root_score = -CHECKMATE
                root_best  = None
                orig_alpha = alpha

                ordered = order_moves(validMoves, d, best_move_so_far)

                for move in ordered:
                    gs.makeMove(move)
                    next_moves = gs.getValidMoves()
                    score = -negamax(gs, next_moves, d - 1,
                                     -beta, -alpha, -turn, deadline,
                                     search_history={})
                    gs.undoMove()

                    if score > root_score:
                        root_score = score
                        root_best  = move

                    if root_score > alpha:
                        alpha = root_score
                    if alpha >= beta:
                        break

                if not use_window:
                    break

                if abs(root_score) >= CHECKMATE_THRESHOLD:
                    note = "mate-found"
                    break

                if root_score <= orig_alpha:
                    widening += 1
                    alpha -= delta * (2 ** min(widening, 4))
                    note   = f"↓w{widening}"
                    continue
                elif root_score >= beta:
                    widening += 1
                    beta  += delta * (2 ** min(widening, 4))
                    note   = f"↑w{widening}"
                    continue
                else:
                    break

            iter_best = root_best

            if prev_score is not None and use_window:
                if abs(root_score - prev_score) < delta * 0.5:
                    stable_depths += 1
                else:
                    stable_depths = 0

            parity_scores[parity] = root_score

        except TimeUp:
            t = time.time() - iter_start
            print(f"  {d:<4} {'(timeout)':<14} {'':>7}  {t:>5.2f}s  ⏱")
            break

        if iter_best is not None:
            best_move_so_far = iter_best

        t        = time.time() - iter_start
        mv_str   = str(best_move_so_far) if best_move_so_far else "None"
        sc_str   = f"{root_score:+.2f}" if root_score is not None else "N/A"
        print(f"  {d:<4} {mv_str:<14} {sc_str:>7}  {t:>5.2f}s  {note}")

    total_time = time.time() - total_start
    board_eval = scoreBoard(gs)
    adv        = "White" if board_eval >= 0 else "Black"
    print(f"  {'─'*48}")
    print(f"  ✅ {best_move_so_far}  |  eval {board_eval:+.2f} ({adv})  |  "
          f"TT {len(transTable):,}  |  {total_time:.2f}s\n")

    return best_move_so_far


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def findBestMove(gs, validMoves, returnQueue=None):
    global nextMove, gameHistory
    nextMove = None

    # Record the current position in game history BEFORE searching.
    # This lets negamax know which positions have already occurred on the board.
    key = _board_key(gs)
    gameHistory[key] = gameHistory.get(key, 0) + 1

    chosen = findMoveIterativeDeepening(gs, validMoves)

    if chosen is None:
        chosen = random.choice(validMoves)

    nextMove = chosen

    if returnQueue is not None:
        returnQueue.put(chosen)
    else:
        return chosen

def notify_undo(gs):
    """Call this when a move is undone so gameHistory stays accurate."""
    key = _board_key(gs)
    if gameHistory.get(key, 0) > 0:
        gameHistory[key] -= 1