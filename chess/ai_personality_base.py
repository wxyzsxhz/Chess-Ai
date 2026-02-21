"""
Base configuration and shared utilities for AI personalities (OPTIMIZED v2)
"""

import random
import time

# CONSTANTS
CHECKMATE = 1000
STALEMATE = 0

# BASE PIECE VALUES
BASE_PIECE_SCORE = {
    "K": 0,
    "Q": 9,
    "R": 5,
    "B": 3,
    "N": 3,
    "p": 1
}

# PIECE-SQUARE TABLES
knightScores = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1]
]

bishopScores = [
    [4, 3, 2, 1, 1, 2, 3, 4],
    [3, 4, 3, 2, 2, 3, 4, 3],
    [2, 3, 4, 3, 3, 4, 3, 2],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [2, 3, 4, 3, 3, 4, 3, 2],
    [3, 4, 3, 2, 2, 3, 4, 3],
    [4, 3, 2, 1, 1, 2, 3, 4]
]

queenScores = [
    [1, 1, 1, 3, 1, 1, 1, 1],
    [1, 2, 3, 3, 3, 1, 1, 1],
    [1, 4, 3, 3, 3, 4, 2, 1],
    [1, 2, 3, 3, 3, 2, 2, 1],
    [1, 2, 3, 3, 3, 2, 2, 1],
    [1, 4, 3, 3, 3, 4, 2, 1],
    [1, 1, 2, 3, 3, 1, 1, 1],
    [1, 1, 1, 3, 1, 1, 1, 1]
]

rookScores = [
    [4, 3, 4, 4, 4, 4, 3, 4],
    [4, 4, 4, 4, 4, 4, 4, 4],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 1, 2, 2, 2, 2, 1, 1],
    [4, 4, 4, 4, 4, 4, 4, 4],
    [4, 3, 2, 1, 1, 2, 3, 4]
]

whitePawnScores = [
    [8, 8, 8, 8, 8, 8, 8, 8],
    [8, 8, 8, 8, 8, 8, 8, 8],
    [5, 6, 6, 7, 7, 6, 6, 5],
    [2, 3, 3, 5, 5, 3, 3, 2],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 1, 1, 0, 0, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0]
]

blackPawnScores = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 1, 1, 1],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [2, 3, 3, 5, 5, 3, 3, 2],
    [5, 6, 6, 7, 7, 6, 6, 5],
    [8, 8, 8, 8, 8, 8, 8, 8],
    [8, 8, 8, 8, 8, 8, 8, 8]
]

BASE_PIECE_POSITION_SCORES = {
    "N": knightScores,
    "B": bishopScores,
    "Q": queenScores,
    "R": rookScores,
    "wp": whitePawnScores,
    "bp": blackPawnScores
}

# TRANSPOSITION TABLE
class TranspositionTable:
    """Improved cache with proper position hashing."""
    def __init__(self, max_size=100000):
        self.table = {}
        self.max_size = max_size
    
    def get(self, position_hash, depth):
        key = (position_hash, depth)
        return self.table.get(key, None)
    
    def store(self, position_hash, depth, score):
        if len(self.table) >= self.max_size:
            keys_to_remove = list(self.table.keys())[:self.max_size // 2]
            for key in keys_to_remove:
                del self.table[key]
        
        key = (position_hash, depth)
        self.table[key] = score
    
    def clear(self):
        self.table.clear()

def get_position_hash(gs):
    """
    IMPROVED hash that includes:
    - Board position
    - Side to move
    - Castling rights
    - En passant square
    """
    board_string = ""
    for row in gs.board:
        for square in row:
            board_string += square
    
    # Add side to move
    board_string += "W" if gs.whiteToMove else "B"
    
    # Add castling rights
    board_string += ("K" if gs.whiteCastleKingside else "-")
    board_string += ("Q" if gs.whiteCastleQueenside else "-")
    board_string += ("k" if gs.blackCastleKingside else "-")
    board_string += ("q" if gs.blackCastleQueenside else "-")
    
    # Add en passant
    if gs.enpasantPossible:
        board_string += f"ep{gs.enpasantPossible[0]}{gs.enpasantPossible[1]}"
    
    return hash(board_string)

# MOVE ORDERING
def order_moves(moves, piece_scores):
    """
    Order moves for better alpha-beta pruning.
    
    Priority:
    1. Pawn promotions (huge value)
    2. Captures of valuable pieces
    3. Other captures
    4. Quiet moves
    """
    def move_score(move):
        score = 0
        
        # Pawn promotion
        if move.isPawnPromotion:
            score += 100
        
        # Captures
        if move.pieceCaptured != '--':
            # MVV-LVA: Most Valuable Victim - Least Valuable Attacker
            victim_value = piece_scores[move.pieceCaptured[1]]
            attacker_value = piece_scores[move.pieceMoved[1]]
            score += 10 * victim_value - attacker_value
        
        return score
    
    return sorted(moves, key=move_score, reverse=True)

# HELPER FUNCTIONS
def findRandomMoves(validMoves):
    return validMoves[random.randint(0, len(validMoves) - 1)]