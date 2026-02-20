"""
Configuration constants and themes for the chess game.
"""

# Board dimensions
BOARD_WIDTH = BOARD_HEIGHT = 640
MOVE_LOG_PANEL_WIDTH = 400
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15

# Board themes
BOARD_THEMES = {
    "Green": {
        "light": (237, 238, 209),
        "dark": (119, 153, 82),
        "panel": (200, 220, 180)  # Pale greenish panel
    },
    "Brown": {
        "light": (240, 217, 181),
        "dark": (181, 136, 99),
        "panel": (220, 200, 170)  # Pale brown panel
    },
    "Gray": {
        "light": (220, 220, 220),
        "dark": (170, 170, 170),
        "panel": (200, 200, 200)  # Pale gray panel
    }
}

# Piece sets
PIECE_SETS = {
    "Classic": "images1/",
    "Modern": "images2/",
    "Wooden": "images3/",
    "Fantasy": "images4/",
}

# Highlight colors
MOVE_HIGHLIGHT_COLOR = (84, 115, 161)
POSSIBLE_MOVE_COLOR = (255, 255, 51)

# Default bot settings
DEFAULT_WHITE_BOT = False
DEFAULT_BLACK_BOT = True

# AI Personality settings
AI_PERSONALITIES = {
    "Fortress": {
        "description": "Defensive, prioritizes king safety",
        "difficulty": "Easy",
        "color": (100, 149, 237)  # Cornflower blue
    },
    "Prophet": {
        "description": "Strategic, thinks long-term",
        "difficulty": "Hard",
        "color": (186, 85, 211)  # Medium orchid
    },
    "Gambler": {
        "description": "Aggressive, takes risks",
        "difficulty": "Easy",
        "color": (220, 20, 60)  # Crimson
    },
    "Tactician": {
        "description": "Short-term, quick attacks",
        "difficulty": "Medium",
        "color": (255, 140, 0)  # Dark orange
    }
}

DEFAULT_AI_PERSONALITY = "Fortress"