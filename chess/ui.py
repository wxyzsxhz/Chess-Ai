"""
UI components for the chess game including menus, drawing functions, and popups.
"""

import sys
import pygame as p
from config import BOARD_WIDTH, BOARD_HEIGHT, SQ_SIZE, DIMENSION, BOARD_THEMES, PIECE_SETS, MOVE_HIGHLIGHT_COLOR, POSSIBLE_MOVE_COLOR
from config import BOARD_THEMES, PIECE_SETS, MOVE_HIGHLIGHT_COLOR, POSSIBLE_MOVE_COLOR, MOVE_LOG_PANEL_WIDTH

IMAGES = {}
FLIP_BOARD = False

# ===============================
# MODERN LIGHT UI COLORS
# ===============================
BG_COLOR = p.Color("#F4F1EA")
PANEL_COLOR = p.Color("#E6E6E6")
ACCENT = p.Color("#2B5DFF")
HOVER = p.Color("#4A7CFF")
DANGER = p.Color("#C62828")

# ===============================
# ANIMATION VARIABLES
# ===============================
ANIMATING = False
ANIM_START = None
ANIM_END = None
ANIM_PIECE = None
ANIM_PROGRESS = 0
ANIM_SPEED = 0.2

# ===============================
# SHARED MENU FONTS
# ===============================
p.font.init()
MENU_TITLE_FONT = p.font.SysFont("Arial", 36, bold=True)
MENU_SUBTITLE_FONT = p.font.SysFont("Arial", 25)
MENU_TEXT_FONT = p.font.SysFont("Arial", 21)
MENU_SMALL_FONT = p.font.SysFont("Arial", 16)

START_BUTTON_Y = 490 # Start button location

def load_images(piece_folder):
    """Load piece images from the specified folder."""
    pieces = ['bR', 'bN', 'bB', 'bQ', 'bK', 'bp', 
              'wR', 'wN', 'wB', 'wQ', 'wK', 'wp']
    for piece in pieces:
        image_path = piece_folder + piece + ".png"
        original_image = p.image.load(image_path)
        IMAGES[piece] = p.transform.smoothscale(original_image, (SQ_SIZE, SQ_SIZE))

def draw_button(screen, rect, text, font, enabled=True):
    mouse_pos = p.mouse.get_pos()
    hovered = rect.collidepoint(mouse_pos)

    if not enabled:
        color = p.Color("gray")
    else:
        color = HOVER if hovered else ACCENT

    p.draw.rect(screen, color, rect, border_radius=8)
    label = font.render(text, True, p.Color("white"))
    screen.blit(label, (
        rect.x + rect.width//2 - label.get_width()//2,
        rect.y + rect.height//2 - label.get_height()//2
    ))

def draw_confirm_button(screen, text, y, enabled):
    font = p.font.SysFont("Arial", 24)
    button_width = 120
    button_height = 60

    button_rect = p.Rect(
        screen.get_width() // 2 - button_width // 2,
        y,
        button_width,
        button_height
    )

    if enabled:
        p.draw.rect(screen, p.Color("green"), button_rect)
    else:
        p.draw.rect(screen, p.Color("gray"), button_rect)

    label = font.render(text, True, p.Color("white"))
    screen.blit(
        label,
        (
            button_rect.x + button_rect.width // 2 - label.get_width() // 2,
            button_rect.y + button_rect.height // 2 - label.get_height() // 2
        )
    )

    return button_rect

def ask_theme(screen):
    """Theme selection screen."""
    font = MENU_TEXT_FONT
    title_font = MENU_TITLE_FONT
    subtitle_font = MENU_SUBTITLE_FONT
    
    selected_board = None
    selected_pieces = None
    
    preview_size = 90
    spacing = 40
    
    while True:
        screen.fill(p.Color("white"))
        
        # Title
        title = title_font.render("Select Game Theme", True, p.Color("black"))
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 40))
        
        # Board themes section
        board_title = subtitle_font.render("Board Themes", True, p.Color("black"))
        screen.blit(board_title, (screen.get_width()//2 - board_title.get_width()//2, 120))

        # Board previews
        board_rects = []
        preview_size = 90
        spacing = 40
        total_width = len(BOARD_THEMES) * preview_size + (len(BOARD_THEMES) - 1) * spacing
        start_x = screen.get_width()//2 - total_width//2
        y = 160
                
        for i, (name, colors_dict) in enumerate(BOARD_THEMES.items()):
            x = start_x + i * (preview_size + spacing)
            preview_rect = p.Rect(x, y, preview_size, preview_size)
            
            # Draw mini board preview
            square_size = preview_size // 4
            for r in range(4):
                for c in range(4):
                    color = colors_dict["light"] if (r + c) % 2 == 0 else colors_dict["dark"]
                    p.draw.rect(screen, color, 
                               p.Rect(x + c * square_size, y + r * square_size, 
                                     square_size, square_size))
            
            # Highlight if selected
            if selected_board == name:
                p.draw.rect(screen, p.Color("red"), preview_rect, 4)
            else:
                p.draw.rect(screen, p.Color("black"), preview_rect, 2)
            
            # Label
            label = font.render(name, True, p.Color("black"))
            label_rect = label.get_rect(center=(x + preview_size//2, y + preview_size + 25))
            screen.blit(label, label_rect)
            
            board_rects.append((preview_rect, name))
        
        # Piece sets section (similar to board themes)
        piece_title = subtitle_font.render("Piece Sets", True, p.Color("black"))
        screen.blit(piece_title, (screen.get_width()//2 - piece_title.get_width()//2, 300))

        y = 340
        total_width = len(PIECE_SETS) * preview_size + (len(PIECE_SETS) - 1) * spacing
        start_x = screen.get_width()//2 - total_width//2
        piece_rects = []
        
        for i, (name, folder) in enumerate(PIECE_SETS.items()):
            x = start_x + i * (preview_size + spacing)
            preview_rect = p.Rect(x, y, preview_size, preview_size)
            
            p.draw.rect(screen, p.Color("lightgray"), preview_rect)
            
            try:
                preview_image = p.image.load(folder + "wK.png")
                preview_image = p.transform.smoothscale(preview_image, (preview_size - 10, preview_size - 10))
                screen.blit(preview_image, (x + 5, y + 5))
            except:
                pass
            
            if selected_pieces == name:
                p.draw.rect(screen, p.Color("red"), preview_rect, 4)
            else:
                p.draw.rect(screen, p.Color("black"), preview_rect, 2)
            
            label = font.render(name, True, p.Color("black"))
            label_rect = label.get_rect(center=(x + preview_size//2, y + preview_size + 25))
            screen.blit(label, label_rect)
            
            piece_rects.append((preview_rect, name))
        
        #BUTTON
        start_button = draw_confirm_button(screen, "CONFIRM", START_BUTTON_Y, selected_board and selected_pieces)
        
        p.display.flip()
        
        # Event handling
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            
            if event.type == p.MOUSEBUTTONDOWN:
                pos = event.pos
                
                for rect, name in board_rects:
                    if rect.collidepoint(pos):
                        selected_board = name
                
                for rect, name in piece_rects:
                    if rect.collidepoint(pos):
                        selected_pieces = name
                
                if start_button.collidepoint(pos) and selected_board and selected_pieces:
                    return selected_board, selected_pieces

def ask_bot_settings(screen):
    """Bot and board orientation selection screen."""
    btn_width, btn_height = 250, 60
    spacing = 40

    center_x = screen.get_width()//2
    total_width = btn_width * 3 + spacing * 2
    start_x = (screen.get_width() - total_width) // 2

    font = MENU_TEXT_FONT
    title_font = MENU_TITLE_FONT
    subtitle_font = MENU_SUBTITLE_FONT
    choosing = True
    
    btn_pvp = p.Rect(start_x, 180, btn_width, btn_height)
    btn_pvb = p.Rect(start_x + btn_width + spacing, 180, btn_width, btn_height)
    btn_bvb = p.Rect(start_x + (btn_width + spacing) * 2, 180, btn_width, btn_height)

    btn_play_white = p.Rect(center_x - btn_width - spacing//2, 340, btn_width, btn_height)
    btn_play_black = p.Rect(center_x + spacing//2, 340, btn_width, btn_height)

    btn_p1_white = p.Rect(center_x - btn_width - spacing//2, 340, btn_width, btn_height)
    btn_p1_black = p.Rect(center_x + spacing//2, 340, btn_width, btn_height)

    # State variables
    game_mode = None
    white_bot = False
    black_bot = False
    flip_board = False
    player_color = None  # Only used in PvB mode: 'white' or 'black'
    
    while choosing:
        screen.fill(p.Color("white"))
        
        title = title_font.render("Game Setup", True, p.Color("black"))
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 40))
        
        # Game Mode Selection
        step1_text = subtitle_font.render("Select Game Mode", True, p.Color("black"))
        screen.blit(step1_text, (screen.get_width()//2 - step1_text.get_width()//2, 140))

        # Player vs Player button
        if game_mode == 'pvp':
            p.draw.rect(screen, p.Color("darkblue"), btn_pvp)
            p.draw.rect(screen, p.Color("blue"), btn_pvp, 4)
        else:
            p.draw.rect(screen, p.Color("lightgray"), btn_pvp)
            p.draw.rect(screen, p.Color("black"), btn_pvp, 2)
        pvp_text = font.render("Player vs Player", True, p.Color("black"))
        screen.blit(pvp_text, (btn_pvp.x + btn_pvp.width//2 - pvp_text.get_width()//2, 
                               btn_pvp.y + 20))
        
        # Player vs Bot button
        if game_mode == 'pvb':
            p.draw.rect(screen, p.Color("darkblue"), btn_pvb)
            p.draw.rect(screen, p.Color("blue"), btn_pvb, 4)
        else:
            p.draw.rect(screen, p.Color("lightgray"), btn_pvb)
            p.draw.rect(screen, p.Color("black"), btn_pvb, 2)
        pvb_text = font.render("Player vs Bot", True, p.Color("black"))
        screen.blit(pvb_text, (btn_pvb.x + btn_pvb.width//2 - pvb_text.get_width()//2, 
                               btn_pvb.y + 20))

        # Bot vs Bot button
        if game_mode == 'bvb':
            p.draw.rect(screen, p.Color("darkblue"), btn_bvb)
            p.draw.rect(screen, p.Color("blue"), btn_bvb, 4)
        else:
            p.draw.rect(screen, p.Color("lightgray"), btn_bvb)
            p.draw.rect(screen, p.Color("black"), btn_bvb, 2)
        bvb_text = font.render("Bot vs Bot", True, p.Color("black"))
        screen.blit(bvb_text, (btn_bvb.x + btn_bvb.width//2 - bvb_text.get_width()//2, 
                            btn_bvb.y + 20))
        
        # Color/Orientation Selection (conditional based on game mode)
        if game_mode:
            if game_mode == 'pvb' or game_mode == 'pvp':  # Only show for PvB and PvP
                step2_text = subtitle_font.render("Select Color/Orientation", True, p.Color("black"))
                screen.blit(step2_text, (screen.get_width()//2 - step2_text.get_width()//2, 300))

                if game_mode == 'pvb':
                    # Play as White button
                    if player_color == 'white':
                        p.draw.rect(screen, p.Color("lightgray"), btn_play_white)
                        p.draw.rect(screen, p.Color("red"), btn_play_white, 4)
                    else:
                        p.draw.rect(screen, p.Color("white"), btn_play_white)
                        p.draw.rect(screen, p.Color("black"), btn_play_white, 2)
                    white_text = font.render("Play as White", True, p.Color("black"))
                    screen.blit(white_text, (btn_play_white.x + btn_play_white.width//2 - white_text.get_width()//2,
                                            btn_play_white.y + 20))
                    
                    # Play as Black button
                    if player_color == 'black':
                        p.draw.rect(screen, p.Color("dimgray"), btn_play_black)
                        p.draw.rect(screen, p.Color("red"), btn_play_black, 4)
                    else:
                        p.draw.rect(screen, p.Color("black"), btn_play_black)
                        p.draw.rect(screen, p.Color("gray"), btn_play_black, 2)
                    black_text = font.render("Play as Black", True, p.Color("white"))
                    screen.blit(black_text, (btn_play_black.x + btn_play_black.width//2 - black_text.get_width()//2,
                                            btn_play_black.y + 20))
                
                elif game_mode == 'pvp':
                    # Player 1 (White) at bottom
                    if not flip_board:
                        p.draw.rect(screen, p.Color("lightgray"), btn_p1_white)
                        p.draw.rect(screen, p.Color("red"), btn_p1_white, 4)
                    else:
                        p.draw.rect(screen, p.Color("white"), btn_p1_white)
                        p.draw.rect(screen, p.Color("black"), btn_p1_white, 2)
                    p1w_text = font.render("White at Bottom", True, p.Color("black"))
                    screen.blit(p1w_text, (btn_p1_white.x + btn_p1_white.width//2 - p1w_text.get_width()//2,
                                        btn_p1_white.y + 20))
                    
                    # Player 2 (Black) at bottom
                    if flip_board:
                        p.draw.rect(screen, p.Color("dimgray"), btn_p1_black)
                        p.draw.rect(screen, p.Color("red"), btn_p1_black, 4)
                    else:
                        p.draw.rect(screen, p.Color("black"), btn_p1_black)
                        p.draw.rect(screen, p.Color("gray"), btn_p1_black, 2)
                    p1b_text = font.render("Black at Bottom", True, p.Color("white"))
                    screen.blit(p1b_text, (btn_p1_black.x + btn_p1_black.width//2 - p1b_text.get_width()//2,
                                        btn_p1_black.y + 20))
        
        # Confirm button
        can_confirm = False
        if game_mode == 'pvp' and (flip_board is not None):
            can_confirm = True
        elif game_mode == 'pvb' and player_color:
            can_confirm = True
        elif game_mode == 'bvb':
            can_confirm = True
        
        confirm_button = draw_confirm_button(screen, "CONFIRM", START_BUTTON_Y, can_confirm)
        
        p.display.flip()
        
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                # Game mode selection
                if btn_pvp.collidepoint(e.pos):
                    game_mode = 'pvp'
                    player_color = None
                    flip_board = False  # Default to white at bottom
                    white_bot = False
                    black_bot = False
                elif btn_pvb.collidepoint(e.pos):
                    game_mode = 'pvb'
                    player_color = None
                    flip_board = False  # Will be set based on player color
                elif btn_bvb.collidepoint(e.pos):
                    game_mode = 'bvb'
                    player_color = None
                    flip_board = False  
                    white_bot = True
                    black_bot = True
                
                # Color/Orientation selection
                if game_mode == 'pvb':
                    if btn_play_white.collidepoint(e.pos):
                        player_color = 'white'
                        white_bot = False
                        black_bot = True
                        flip_board = False  # Player (white) at bottom
                    elif btn_play_black.collidepoint(e.pos):
                        player_color = 'black'
                        white_bot = True
                        black_bot = False
                        flip_board = True  # Player (black) at bottom
                
                elif game_mode == 'pvp':
                    if btn_p1_white.collidepoint(e.pos):
                        flip_board = False
                    elif btn_p1_black.collidepoint(e.pos):
                        flip_board = True
                
                # Confirm
                if confirm_button.collidepoint(e.pos) and can_confirm:
                    choosing = False
    
    return white_bot, black_bot, flip_board

def ask_bvb_personalities(screen):
    """
    Bot vs Bot personality selection - select both White and Black personalities.
    """
    from config import AI_PERSONALITIES
    
    font = MENU_TEXT_FONT
    title_font = MENU_TITLE_FONT
    desc_font = MENU_SMALL_FONT 
    
    white_personality = None
    black_personality = None
    
    # Button dimensions
    button_width = 220
    button_height = 100
    spacing = 15
    cols = 2
    rows = 2

    section_gap = 60  # gap between white and black sections
    section_width = cols * button_width + (cols - 1) * spacing
    total_width = section_width * 2 + section_gap
    left_margin = (screen.get_width() - total_width) // 2

    # White section (left side)
    white_start_x = left_margin
    white_start_y = 185
    
    # Black section (right side)
    black_start_x = left_margin + section_width + section_gap
    black_start_y = 185
        
    while True:
        screen.fill(p.Color("white"))
        
        # Main title
        title = title_font.render("Select Personalities for Bots", True, p.Color("black"))
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 30))
        
        # Divider line between sections
        divider_x = left_margin + section_width + section_gap // 2

        # Section titles — centered over each grid
        white_section_center = white_start_x + section_width // 2
        black_section_center = black_start_x + section_width // 2

        # Section titles
        white_title = font.render("WHITE BOT", True, p.Color("black"))
        screen.blit(white_title, (white_section_center - white_title.get_width()//2, 130))
        
        black_title = font.render("BLACK BOT", True, p.Color("black"))
        screen.blit(black_title, (black_section_center - black_title.get_width()//2, 130))
        
        # Draw personality buttons
        white_buttons = []
        black_buttons = []
        personalities = list(AI_PERSONALITIES.keys())
        
        for i, personality_name in enumerate(personalities):
            row = i // 2
            col = i % 2
            
            personality_data = AI_PERSONALITIES[personality_name]
            
            # White bot buttons (left side)
            white_x = white_start_x + col * (button_width + spacing)
            white_y = white_start_y + row * (button_height + spacing)
            white_rect = p.Rect(white_x, white_y, button_width, button_height)
            
            if white_personality == personality_name:
                p.draw.rect(screen, p.Color(*personality_data["color"]), white_rect)
                p.draw.rect(screen, p.Color("gold"), white_rect, 5)
            else:
                color = personality_data["color"]
                light_color = tuple(min(c + 80, 255) for c in color)
                p.draw.rect(screen, p.Color(*light_color), white_rect)
                p.draw.rect(screen, p.Color("black"), white_rect, 2)
            
            name_text = font.render(personality_name, True, p.Color("white"))
            screen.blit(name_text, (white_x + button_width//2 - name_text.get_width()//2, white_y + 20))
            
            desc_text = desc_font.render(personality_data["description"], True, p.Color("white"))
            screen.blit(desc_text, (white_x + button_width//2 - desc_text.get_width()//2, white_y + 50))
            
            white_buttons.append((white_rect, personality_name))
            
            # Black bot buttons (right side)
            black_x = black_start_x + col * (button_width + spacing)
            black_y = black_start_y + row * (button_height + spacing)
            black_rect = p.Rect(black_x, black_y, button_width, button_height)
            
            if black_personality == personality_name:
                p.draw.rect(screen, p.Color(*personality_data["color"]), black_rect)
                p.draw.rect(screen, p.Color("gold"), black_rect, 5)
            else:
                color = personality_data["color"]
                light_color = tuple(min(c + 80, 255) for c in color)
                p.draw.rect(screen, p.Color(*light_color), black_rect)
                p.draw.rect(screen, p.Color("black"), black_rect, 2)
            
            name_text = font.render(personality_name, True, p.Color("white"))
            screen.blit(name_text, (black_x + button_width//2 - name_text.get_width()//2, black_y + 20))
            
            desc_text = desc_font.render(personality_data["description"], True, p.Color("white"))
            screen.blit(desc_text, (black_x + button_width//2 - desc_text.get_width()//2, black_y + 50))
            
            black_buttons.append((black_rect, personality_name))
        
        confirm_button = draw_confirm_button(screen, "CONFIRM", START_BUTTON_Y, white_personality and black_personality)
        
        p.display.flip()
        
        # Event handling
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            
            if event.type == p.MOUSEBUTTONDOWN:
                pos = event.pos
                
                # Check white bot buttons
                for button_rect, personality_name in white_buttons:
                    if button_rect.collidepoint(pos):
                        white_personality = personality_name
                
                # Check black bot buttons
                for button_rect, personality_name in black_buttons:
                    if button_rect.collidepoint(pos):
                        black_personality = personality_name
                
                # Check confirm button
                if confirm_button.collidepoint(pos) and white_personality and black_personality:
                    return white_personality, black_personality

def ask_ai_personality(screen):
    """AI Personality selection screen."""
    from config import AI_PERSONALITIES
    
    font = MENU_TEXT_FONT
    title_font = MENU_TITLE_FONT
    subtitle_font = MENU_SUBTITLE_FONT
    desc_font = MENU_SMALL_FONT
    
    selected_personality = None
    
    # Button dimensions
    button_width = 280
    button_height = 120
    spacing = 30
    cols = 2
    rows = 2

    total_width = cols*button_width + (cols-1)*spacing
    total_height = rows*button_height + (rows-1)*spacing

    start_x = screen.get_width()//2 - total_width//2
    start_y = screen.get_height()//2 - total_height//2 - 35
    
    while True:
        screen.fill(p.Color("white"))
        
        # Title
        title = title_font.render("Select AI Personality", True, p.Color("black"))
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 40))
        
        # Subtitle
        subtitle = subtitle_font.render("Choose how the AI plays", True, p.Color("black"))
        screen.blit(subtitle, (screen.get_width()//2 - subtitle.get_width()//2, 85))
        
        # Draw personality buttons in 2x2 grid
        personality_buttons = []
        personalities = list(AI_PERSONALITIES.keys())
        
        for i, personality_name in enumerate(personalities):
            row = i // 2
            col = i % 2
            
            x = start_x + col*(button_width + spacing)
            y = start_y + row*(button_height + spacing)
            
            button_rect = p.Rect(x, y, button_width, button_height)
            personality_data = AI_PERSONALITIES[personality_name]
            
            # Draw button background
            if selected_personality == personality_name:
                # Selected - draw with personality color and thick border
                p.draw.rect(screen, p.Color(*personality_data["color"]), button_rect)
                p.draw.rect(screen, p.Color("gold"), button_rect, 5)
            else:
                # Not selected - lighter version
                color = personality_data["color"]
                light_color = tuple(min(c + 60, 255) for c in color)
                p.draw.rect(screen, p.Color(*light_color), button_rect)
                p.draw.rect(screen, p.Color("black"), button_rect, 2)
            
            # Draw personality name
            name_text = title_font.render(personality_name, True, p.Color(100, 100, 100))
            name_rect = name_text.get_rect(center=(x + button_width//2, y + 30))
            screen.blit(name_text, name_rect)
            
            # Draw description
            desc_text = desc_font.render(personality_data["description"], True, p.Color("white"))
            desc_rect = desc_text.get_rect(center=(x + button_width//2, y + 60))
            screen.blit(desc_text, desc_rect)
            
            # Draw difficulty badge
            diff_text = font.render(f"{personality_data['difficulty']}", True, p.Color("yellow"))
            diff_rect = diff_text.get_rect(center=(x + button_width//2, y + 90))
            screen.blit(diff_text, diff_rect)
            
            personality_buttons.append((button_rect, personality_name))
        
        confirm_button = draw_confirm_button(screen, "CONFIRM", START_BUTTON_Y, selected_personality)

        p.display.flip()
        
        # Event handling
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            
            if event.type == p.MOUSEBUTTONDOWN:
                pos = event.pos
                
                # Check personality button clicks
                for button_rect, personality_name in personality_buttons:
                    if button_rect.collidepoint(pos):
                        selected_personality = personality_name
                
                # Check confirm button
                if confirm_button.collidepoint(pos) and selected_personality:
                    return selected_personality

def pawn_promotion_popup(screen, gs):
    """Pawn promotion selection popup."""
    font = p.font.SysFont("Times New Roman", 30, False, False)
    text = font.render("Choose promotion:", True, p.Color("black"))
    
    button_width, button_height = 100, 100
    buttons = [
        p.Rect(100, 200, button_width, button_height),
        p.Rect(200, 200, button_width, button_height),
        p.Rect(300, 200, button_width, button_height),
        p.Rect(400, 200, button_width, button_height)
    ]
    
    if gs.whiteToMove:
        button_images = [
            p.transform.smoothscale(p.image.load("images1/bQ.png"), (100, 100)),
            p.transform.smoothscale(p.image.load("images1/bR.png"), (100, 100)),
            p.transform.smoothscale(p.image.load("images1/bB.png"), (100, 100)),
            p.transform.smoothscale(p.image.load("images1/bN.png"), (100, 100))
        ]
    else:
        button_images = [
            p.transform.smoothscale(p.image.load("images1/wQ.png"), (100, 100)),
            p.transform.smoothscale(p.image.load("images1/wR.png"), (100, 100)),
            p.transform.smoothscale(p.image.load("images1/wB.png"), (100, 100)),
            p.transform.smoothscale(p.image.load("images1/wN.png"), (100, 100))
        ]
    
    while True:
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.collidepoint(e.pos):
                        return ["Q", "R", "B", "N"][i]
        
        screen.fill(p.Color("white"))
        screen.blit(text, (110, 150))
        
        for i, button in enumerate(buttons):
            p.draw.rect(screen, p.Color("white"), button)
            screen.blit(button_images[i], button.topleft)
        
        p.display.flip()

def draw_board(screen, light_color, dark_color):
    colors = [p.Color(light_color), p.Color(dark_color)]
    font = p.font.SysFont("Arial", 16, True)

    for row in range(8):
        for col in range(8):
            color = colors[(row + col) % 2]

            draw_row = 7 - row if FLIP_BOARD else row
            draw_col = 7 - col if FLIP_BOARD else col

            p.draw.rect(
                screen,
                color,
                p.Rect(draw_col * SQ_SIZE, draw_row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            )

    # -------- Draw Coordinates --------
    files = ['A','B','C','D','E','F','G','H']
    ranks = ['1','2','3','4','5','6','7','8']

    if FLIP_BOARD:
        files = files[::-1]
        ranks = ranks[::-1]

    # Draw letters (bottom)
    for col in range(8):
        text = font.render(files[col], True, p.Color("black"))
        x = col * SQ_SIZE + SQ_SIZE - 18
        y = BOARD_HEIGHT - 18
        screen.blit(text, (x, y))

    # Draw numbers (left)
    for row in range(8):
        text = font.render(ranks[7 - row], True, p.Color("black"))
        x = 5
        y = row * SQ_SIZE + 5
        screen.blit(text, (x, y))

def draw_pieces(screen, board):
    global ANIMATING, ANIM_PROGRESS

    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                draw_row = 7 - row if FLIP_BOARD else row
                draw_col = 7 - col if FLIP_BOARD else col
                screen.blit(IMAGES[piece],
                            p.Rect(draw_col * SQ_SIZE, draw_row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    if ANIMATING:
        ANIM_PROGRESS += ANIM_SPEED
        if ANIM_PROGRESS >= 1:
            ANIMATING = False
            ANIM_PROGRESS = 0
        else:
            x = ANIM_START[0] + (ANIM_END[0] - ANIM_START[0]) * ANIM_PROGRESS
            y = ANIM_START[1] + (ANIM_END[1] - ANIM_START[1]) * ANIM_PROGRESS
            screen.blit(IMAGES[ANIM_PIECE], (x, y))

def draw_coordinates(screen):
    font = p.font.SysFont("Arial", 16, True)
    letters = ['A','B','C','D','E','F','G','H']
    numbers = ['1','2','3','4','5','6','7','8']

    if FLIP_BOARD:
        letters = letters[::-1]
        numbers = numbers[::-1]

    offset = 5  # padding from the board edge
    # Draw letters (files) - top and bottom
    for i in range(8):
        # Top
        text = font.render(letters[i], True, p.Color("black"))
        x_top = i * SQ_SIZE + SQ_SIZE//2 - text.get_width()//2
        y_top = -offset - text.get_height()  # above the board
        screen.blit(text, (x_top, y_top))

        # Bottom
        text = font.render(letters[i], True, p.Color("black"))
        x_bot = i * SQ_SIZE + SQ_SIZE//2 - text.get_width()//2
        y_bot = BOARD_HEIGHT + offset  # below the board
        screen.blit(text, (x_bot, y_bot))

    # Draw numbers (ranks) - left and right
    for i in range(8):
        # Left
        text = font.render(numbers[7 - i], True, p.Color("black"))
        x_left = -offset - text.get_width()  # left of the board
        y_left = i * SQ_SIZE + SQ_SIZE//2 - text.get_height()//2
        screen.blit(text, (x_left, y_left))

        # Right
        text = font.render(numbers[7 - i], True, p.Color("black"))
        x_right = BOARD_WIDTH + offset  # right of the board
        y_right = i * SQ_SIZE + SQ_SIZE//2 - text.get_height()//2
        screen.blit(text, (x_right, y_right))


def highlight_squares(screen, gs, valid_moves, square_selected):
    """Highlight selected square and possible moves."""
    if square_selected and gs.board[square_selected[0]][square_selected[1]][0] == ('w' if gs.whiteToMove else 'b'):
        row, col = square_selected
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(100)
        
        # Highlight selected square
        s.fill(p.Color(MOVE_HIGHLIGHT_COLOR))
        draw_row = 7 - row if FLIP_BOARD else row
        draw_col = 7 - col if FLIP_BOARD else col
        screen.blit(s, (draw_col * SQ_SIZE, draw_row * SQ_SIZE))
        
        # Highlight valid moves
        s.fill(p.Color(POSSIBLE_MOVE_COLOR))
        for move in valid_moves:
            if move.startRow == row and move.startCol == col:
                # Apply board flip to the destination squares as well
                end_draw_row = 7 - move.endRow if FLIP_BOARD else move.endRow
                end_draw_col = 7 - move.endCol if FLIP_BOARD else move.endCol
                screen.blit(s, (end_draw_col * SQ_SIZE, end_draw_row * SQ_SIZE))

def draw_evaluation_bar(screen, score):
    bar_x = BOARD_WIDTH + 230
    bar_width = 25
    bar_height = BOARD_HEIGHT

    p.draw.rect(screen, p.Color("black"), (bar_x, 0, bar_width, bar_height), 2)

    score = max(-5, min(5, score))
    ratio = (score + 5) / 10
    white_height = bar_height * ratio

    p.draw.rect(screen, p.Color("white"),
                (bar_x, bar_height - white_height, bar_width, white_height))


def draw_move_log(screen, gs, font, panel_color):
    """Draw the move log panel."""
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT)
    # Accept either tuple or pygame.Color
    if not isinstance(panel_color, p.Color):
        panel_color = p.Color(panel_color)
    p.draw.rect(screen, panel_color, move_log_rect)
      
    move_texts = []
    for i in range(0, len(gs.moveLog), 2):
        move_string = f" {i//2 + 1}. {gs.moveLog[i]} "
        if i + 1 < len(gs.moveLog):
            move_string += str(gs.moveLog[i + 1])
        move_texts.append(move_string)
    
    padding = 10
    line_spacing = 5
    text_y = padding
    
    for i in range(0, len(move_texts), 3):
        text = "".join(move_texts[i:i+3])
        text_obj = font.render(text, True, p.Color('black'))
        screen.blit(text_obj, move_log_rect.move(padding, text_y))
        text_y += text_obj.get_height() + line_spacing

def draw_end_game_text(screen, text):
    """Draw end game message."""
    font = p.font.SysFont("Times New Roman", 30, False, False)
    text_obj = font.render(text, True, p.Color('black'))
    
    text_x = BOARD_WIDTH // 2 - text_obj.get_width() // 2
    text_y = BOARD_HEIGHT // 2 - text_obj.get_height() // 2
    
    screen.blit(text_obj, (text_x, text_y))
    screen.blit(font.render(text, 0, p.Color('Black')), (text_x + 1, text_y + 1))

def set_flip_board(value):
    """Set the board flip state."""
    global FLIP_BOARD
    FLIP_BOARD = value


def draw_ai_debug_info(screen, gs, ai_personality, white_bot, black_bot,
                       time_left=None, human_turn=False, 
                       white_ai_personality=None, black_ai_personality=None):
    """
    Draw AI evaluation debug info panel with timer on top, horizontally centered.
    Timer updates every frame for human turns.
    """
    # Determine which personality to display
    current_personality = None
    
    if white_ai_personality and black_ai_personality:
        # Bot vs Bot mode - show the bot whose turn it is
        current_personality = white_ai_personality if gs.whiteToMove else black_ai_personality
    elif ai_personality:
        # Single bot mode
        current_personality = ai_personality
    
    # If no bot is playing and it's not human turn, don't show anything
    if not current_personality and not human_turn:
        return None

    try:
        font = p.font.SysFont("Courier New", 11)
        bold_font = p.font.SysFont("Arial", 14, bold=True)
        panel_width = 230
        panel_height = 120
        debug_y = BOARD_HEIGHT - 200  # vertical base

        # --- Horizontal center the panel in the MOVE_LOG_PANEL ---
        panel_x = BOARD_WIDTH + (MOVE_LOG_PANEL_WIDTH - panel_width) // 2
        debug_rect = p.Rect(panel_x, debug_y, panel_width, panel_height)

        # Draw panel background and border
        p.draw.rect(screen, p.Color(250, 250, 250), debug_rect)
        p.draw.rect(screen, p.Color("darkblue"), debug_rect, 2)

        # --- Timer on top for human turns ---
        if human_turn and time_left is not None:
            timer_font = p.font.SysFont("Arial", 20, True)

            display_time = int(time_left)

            timer_text = timer_font.render(
                f"Time: {display_time}s",
                True,
                p.Color("red") if display_time <= 5 else p.Color("black")
            )

            # Position inside debug panel
            screen.blit(timer_text, (debug_rect.x + 10, debug_rect.y + 10))

        # --- AI info below timer ---
        if current_personality:
            # Load AI evaluation
            if current_personality == "Fortress":
                import ai_fortress
                raw_score = ai_fortress.scoreBoard(gs)
                depth = ai_fortress.DEPTH
                traits = ["🛡️ King Safety: HIGH", "♟️ Pawn Value: +30%"]
            elif current_personality == "Prophet":
                import ai_prophet
                raw_score = ai_prophet.scoreBoard(gs)
                depth = ai_prophet.DEPTH
                traits = ["🔮 Deep Thinking", "📍 Position: x3"]
            elif current_personality == "Gambler":
                import ai_gambler
                raw_score = getattr(ai_gambler, 'scoreBoard', lambda x: 0)(gs)
                depth = getattr(ai_gambler, 'DEPTH', 4)
                traits = ["🎲 Probabilistic", "⚔️ Aggressive"]
            elif current_personality == "Tactician":
                import ai_tactician
                raw_score = getattr(ai_tactician, 'scoreBoard', lambda x: 0)(gs)
                depth = getattr(ai_tactician, 'DEPTH', 3)
                traits = ["⚔️ Short-term", "💥 Captures: x1.5"]
            else:
                return debug_rect

            # Adjust score based on bot/human
            if white_bot and not black_bot:
                score = -raw_score
            elif black_bot and not white_bot:
                score = raw_score
            else:
                score = raw_score

            content_y = debug_rect.y + 30
            title = bold_font.render(f"{current_personality} AI", True, p.Color("darkblue"))
            screen.blit(title, (debug_rect.x + 10, content_y))

            depth_color = p.Color("purple") if depth >= 5 else (p.Color("red") if depth <= 3 else p.Color("blue"))
            depth_text = font.render(f"Depth: {depth} moves", True, depth_color)
            screen.blit(depth_text, (debug_rect.x + 10, content_y + 20))

            eval_color = p.Color("green") if score > 0 else (p.Color("red") if score < 0 else p.Color("gray"))
            eval_text = font.render(f"Eval: {score:.2f}", True, eval_color)
            screen.blit(eval_text, (debug_rect.x + 10, content_y + 38))

            y_offset = content_y + 56
            for trait in traits[:2]:
                trait_text = font.render(trait, True, p.Color("black"))
                screen.blit(trait_text, (debug_rect.x + 10, y_offset))
                y_offset += 15

        return debug_rect

    except Exception as e:
        print("Error in draw_ai_debug_info:", e)
        return None


def draw_game_menu_buttons(screen, debug_rect):
    """Draw Start and Quit buttons in a horizontal row below debug panel, centered."""

    font = p.font.SysFont("Arial", 12)
    button_width = 60
    button_height = 30
    spacing = 10
    total_width = button_width * 2 + spacing  # only two buttons now

    # Horizontal center relative to debug panel
    if debug_rect:
        x_start = debug_rect.x + (debug_rect.width - total_width) // 2
        y_start = debug_rect.y + debug_rect.height + 10
    else:
        x_start = BOARD_WIDTH + 20
        y_start = 20

    start_btn = p.Rect(x_start, y_start, button_width, button_height)
    quit_btn = p.Rect(x_start + button_width + spacing, y_start, button_width, button_height)

    draw_button(screen, start_btn, "RESTART", font, True)
    draw_button(screen, quit_btn, "QUIT", font, True)

    return start_btn, quit_btn
