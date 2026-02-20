"""
Main game loop for the chess game.
"""

import sys
import pygame as p
from multiprocessing import Process, Queue

# Import all needed constants and functions
from config import (
    BOARD_WIDTH, BOARD_HEIGHT, MOVE_LOG_PANEL_WIDTH, SQ_SIZE, MAX_FPS,
    BOARD_THEMES, PIECE_SETS
)
from ui import (
    IMAGES, draw_coordinates, draw_game_menu_buttons, load_images, ask_theme, ask_bot_settings, pawn_promotion_popup,
    draw_board, draw_pieces, highlight_squares, draw_move_log,
    draw_end_game_text, set_flip_board, draw_ai_debug_info
)
from sound import SoundManager
from engine import GameState, Move
from chessAi import findRandomMoves

# Define these here since they're set at runtime
LIGHT_SQUARE_COLOR = None
DARK_SQUARE_COLOR = None
TURN_TIME_LIMIT = 30  # seconds
SUGGESTION_TIME = 15  # seconds - when to show suggestion


def animate_move(move, screen, board, clock, flip_board, sound_manager, light_color, dark_color, selected_board):
    """Animate a piece moving."""
    colors = [p.Color(light_color), p.Color(dark_color)]
    
    delta_row = move.endRow - move.startRow
    delta_col = move.endCol - move.startCol
    frames_per_square = 5
    frame_count = (abs(delta_row) + abs(delta_col)) * frames_per_square
    
    for frame in range(frame_count + 1):
        row = move.startRow + delta_row * frame / frame_count
        col = move.startCol + delta_col * frame / frame_count
        
        draw_board(screen, light_color, dark_color)
        draw_pieces(screen, board)
        draw_coordinates(screen) 
        # Draw destination square
        end_row = 7 - move.endRow if flip_board else move.endRow
        end_col = 7 - move.endCol if flip_board else move.endCol
        # Draw the panel fully with the theme color
        panel_color = BOARD_THEMES[selected_board]["panel"]
        p.draw.rect(screen, panel_color, p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    
        # for r in range(8):
        #     for c in range(8):
        #         color = light_color if (r + c) % 2 == 0 else dark_color
        #         p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

        # Draw captured piece if any
        if move.pieceCaptured != '--':
            capture_row = move.endRow
            if move.isEnpassantMove:
                capture_row = move.endRow + 1 if move.pieceCaptured[0] == 'b' else move.endRow - 1
            
            draw_capture_row = 7 - capture_row if flip_board else capture_row
            draw_capture_col = 7 - move.endCol if flip_board else move.endCol
            
            screen.blit(IMAGES[move.pieceCaptured],
                       p.Rect(draw_capture_col * SQ_SIZE, draw_capture_row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        
        # Draw moving piece
        draw_row = 7 - row if flip_board else row
        draw_col = 7 - col if flip_board else col
        screen.blit(IMAGES[move.pieceMoved],
                   p.Rect(draw_col * SQ_SIZE, draw_row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        
        p.display.flip()
        clock.tick(240)


def main():
    global LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR
    
    p.init()
    total_width = BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH
    screen = p.display.set_mode((total_width, BOARD_HEIGHT))
    #screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    move_log_font = p.font.SysFont("Times New Roman", 12, False, False)
    sound_manager = SoundManager()
    
    # Initial setup
    selected_board, selected_pieces = ask_theme(screen)
    LIGHT_SQUARE_COLOR = BOARD_THEMES[selected_board]["light"]
    DARK_SQUARE_COLOR = BOARD_THEMES[selected_board]["dark"]
    load_images(PIECE_SETS[selected_pieces])
    
    white_bot, black_bot, flip_board = ask_bot_settings(screen)
    set_flip_board(flip_board)

    # NEW: Ask for AI personality if bot is playing
    ai_personality = None
    findBestMove = None  # Will hold the AI function
    
    if white_bot or black_bot:
        from ui import ask_ai_personality
        ai_personality = ask_ai_personality(screen)
        
        # Import the correct AI module based on selection
        if ai_personality == "Fortress":
            import ai_fortress
            findBestMove = ai_fortress.findBestMove
            print(f"✓ Loaded Fortress AI (Defensive)")
        elif ai_personality == "Prophet":
            import ai_prophet
            findBestMove = ai_prophet.findBestMove
            print(f"✓ Loaded Prophet AI (Strategic)")
        elif ai_personality == "Gambler":
            import ai_gambler
            findBestMove = ai_gambler.findBestMove
            print(f"✓ Loaded Gambler AI (Aggressive)")
        elif ai_personality == "Tactician":
            import ai_tactician
            findBestMove = ai_tactician.findBestMove
            print(f"✓ Loaded Tactician AI (Short-term)")
        else:
            # Fallback to default
            from chessAi import findBestMove
            print(f"⚠ Unknown personality, using default AI")
    
    # Game state
    gs = GameState()
    valid_moves = gs.getValidMoves()
    square_selected = ()
    player_clicks = []
    move_made = False
    animate = False
    game_over = False
    ai_thinking = False
    move_finder_process = None
    move_undone = False

    turn_start_time = p.time.get_ticks()  # milliseconds
    time_left = TURN_TIME_LIMIT

    
    # Draw tracking
    position_history = ""
    previous_pos = ""
    count_moves = 0
    draw_count = 0
    timer_font = p.font.SysFont("Arial", 20, True)
    
    # Suggestion system for human players
    suggestion_move = None
    suggestion_requested = False

    # Initialize buttons
    start_btn = None
    quit_btn = None

    while True:

        human_turn = (gs.whiteToMove and not white_bot) or \
             (not gs.whiteToMove and not black_bot)

        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()

            elif e.type == p.MOUSEBUTTONDOWN:
                mouse_pos = p.mouse.get_pos()

                # Menu buttons
                if start_btn and start_btn.collidepoint(mouse_pos):
                    # --- Full reset: theme, pieces, game setup, AI personality ---
                    selected_board, selected_pieces = ask_theme(screen)
                    LIGHT_SQUARE_COLOR = BOARD_THEMES[selected_board]["light"]
                    DARK_SQUARE_COLOR = BOARD_THEMES[selected_board]["dark"]
                    load_images(PIECE_SETS[selected_pieces])

                    # Ask for bot setup
                    white_bot, black_bot, flip_board = ask_bot_settings(screen)
                    set_flip_board(flip_board)

                    # AI personality
                    ai_personality = None
                    findBestMove = None
                    if white_bot or black_bot:
                        from ui import ask_ai_personality
                        ai_personality = ask_ai_personality(screen)
                        if ai_personality == "Fortress":
                            import ai_fortress
                            findBestMove = ai_fortress.findBestMove
                        elif ai_personality == "Prophet":
                            import ai_prophet
                            findBestMove = ai_prophet.findBestMove
                        elif ai_personality == "Gambler":
                            import ai_gambler
                            findBestMove = ai_gambler.findBestMove
                        elif ai_personality == "Tactician":
                            import ai_tactician
                            findBestMove = ai_tactician.findBestMove

                    # Reset game state
                    gs = GameState()
                    valid_moves = gs.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    suggestion_move = None
                    suggestion_requested = False
                    turn_start_time = p.time.get_ticks()


                elif quit_btn and quit_btn.collidepoint(mouse_pos):
                    p.quit()
                    sys.exit()

                # Board clicks
                elif not game_over and human_turn:
                    col = mouse_pos[0] // SQ_SIZE
                    row = mouse_pos[1] // SQ_SIZE
                    if flip_board:
                        row = 7 - row
                        col = 7 - col

                    if col >= 8:
                        square_selected = ()
                        player_clicks = []
                    elif square_selected == (row, col):
                        square_selected = ()
                        player_clicks = []
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)

                    if len(player_clicks) == 2:
                        move = Move(player_clicks[0], player_clicks[1], gs.board)

                        for valid_move in valid_moves:
                            if move == valid_move:

                                piece_captured = gs.board[valid_move.endRow][valid_move.endCol] != '--'

                                gs.makeMove(valid_move)

                                if valid_move.isPawnPromotion:
                                    promotion = pawn_promotion_popup(screen, gs)
                                    gs.board[valid_move.endRow][valid_move.endCol] = valid_move.pieceMoved[0] + promotion
                                    sound_manager.play_promote()
                                    piece_captured = False
                                elif piece_captured or valid_move.isEnpassantMove:
                                    sound_manager.play_capture()
                                else:
                                    sound_manager.play_move()

                                move_made = True
                                animate = True
                                square_selected = ()
                                player_clicks = []
                                break

                        if not move_made:
                            player_clicks = [square_selected]

                    
                move_undone = False

                # Display suggestion move if available (only for human turns)
                if human_turn and suggestion_move is not None and not game_over:
                    # Highlight the suggested move with a different color
                    s = p.Surface((SQ_SIZE, SQ_SIZE))
                    s.set_alpha(150)
                    s.fill(p.Color("yellow"))
                    
                    # Highlight start square
                    start_draw_row = 7 - suggestion_move.startRow if flip_board else suggestion_move.startRow
                    start_draw_col = 7 - suggestion_move.startCol if flip_board else suggestion_move.startCol
                    screen.blit(s, (start_draw_col * SQ_SIZE, start_draw_row * SQ_SIZE))
                    
                    # Highlight end square
                    end_draw_row = 7 - suggestion_move.endRow if flip_board else suggestion_move.endRow
                    end_draw_col = 7 - suggestion_move.endCol if flip_board else suggestion_move.endCol
                    screen.blit(s, (end_draw_col * SQ_SIZE, end_draw_row * SQ_SIZE))

                # Check game over conditions
                if game_over:
                    if gs.checkmate:
                        text = 'Black wins by checkmate' if gs.whiteToMove else 'White wins by checkmate'
                    elif gs.stalemate:
                        text = 'Stalemate'
                    elif draw_count == 1:
                        text = 'Draw due to repetition'
                    draw_end_game_text(screen, text)
                
        # ===============================
        # UPDATE TIMER EVERY FRAME
        # ===============================

        if human_turn and not game_over:
            elapsed = (p.time.get_ticks() - turn_start_time) / 1000
            time_left = max(0, TURN_TIME_LIMIT - elapsed)
        else:
            time_left = TURN_TIME_LIMIT

        # ===============================
        # GAME LOGIC EVERY FRAME
        # ===============================

        # AI move handling (for bot turns only)
        if not game_over and not human_turn and not move_undone:
                    if not ai_thinking:
                        ai_thinking = True
                        return_queue = Queue()
                        move_finder_process = Process(target=findBestMove, 
                                                    args=(gs, valid_moves, return_queue))
                        move_finder_process.start()
                    
                    if not move_finder_process.is_alive():
                        ai_move = return_queue.get()
                        if ai_move is None:
                            ai_move = findRandomMoves(valid_moves)
                        
                        piece_captured = gs.board[ai_move.endRow][ai_move.endCol] != '--'
                        gs.makeMove(ai_move)
                        
                        if ai_move.isPawnPromotion:
                            promotion = pawn_promotion_popup(screen, gs)
                            gs.board[ai_move.endRow][ai_move.endCol] = ai_move.pieceMoved[0] + promotion
                            sound_manager.play_promote()
                            piece_captured = False
                        
                        if piece_captured or ai_move.isEnpassantMove:
                            sound_manager.play_capture()
                        elif not ai_move.isPawnPromotion:
                            sound_manager.play_move()
                        
                        ai_thinking = False
                        move_made = True
                        animate = True
                        square_selected = ()
                        player_clicks = []
                        
        # Human player timer and suggestion system
        if not game_over and human_turn and not move_undone:
                    # At 15 seconds, start computing a suggestion move
                    if time_left <= SUGGESTION_TIME and not suggestion_requested and suggestion_move is None:
                        suggestion_requested = True
                        suggestion_move = findRandomMoves(valid_moves) 
                    
                    # At 0 seconds, force the suggested move (or random if no suggestion)
                    if time_left == 0:
                        if suggestion_move is None:
                            auto_move = findRandomMoves(valid_moves)
                        else:
                            auto_move = suggestion_move
                        
                        piece_captured = gs.board[auto_move.endRow][auto_move.endCol] != '--'
                        gs.makeMove(auto_move)
                        
                        if auto_move.isPawnPromotion:
                            gs.board[auto_move.endRow][auto_move.endCol] = auto_move.pieceMoved[0] + 'Q'
                            sound_manager.play_promote()
                            piece_captured = False
                        
                        if piece_captured or auto_move.isEnpassantMove:
                            sound_manager.play_capture()
                        elif not auto_move.isPawnPromotion:
                            sound_manager.play_move()
                        
                        move_made = True
                        animate = True
                        square_selected = ()
                        player_clicks = []
                        suggestion_move = None
                        suggestion_requested = False
                        
        # Update game state after move
        if move_made:
                    
                    # Draw detection
                    if count_moves < 4:
                        count_moves += 1
                    if count_moves == 4:
                        position_history += gs.getBoardString()
                        if previous_pos == position_history:
                            draw_count += 1
                            position_history = ""
                            count_moves = 0
                        else:
                            previous_pos = position_history
                            position_history = ""
                            count_moves = 0
                            draw_count = 0
                    
                    if animate:
                        animate_move(gs.moveLog[-1], screen, gs.board, clock, flip_board, sound_manager,
                                LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR, selected_board)
                    
                    valid_moves = gs.getValidMoves()
                    if len(valid_moves) == 0:
                        game_over = True
                    
                    turn_start_time = p.time.get_ticks()
                    suggestion_move = None
                    suggestion_requested = False

                    move_made = False
                    animate = False
                    move_undone = False
        
        # ===============================
        # DRAW GAME EVERY FRAME
        # ===============================
        draw_board(screen, LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR)
        highlight_squares(screen, gs, valid_moves, square_selected)
        draw_pieces(screen, gs.board)

        panel_color = BOARD_THEMES[selected_board]["panel"]
        panel_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT)
        p.draw.rect(screen, panel_color, panel_rect)

        draw_move_log(screen, gs, move_log_font, panel_color)

        debug_rect = draw_ai_debug_info(
            screen, gs, ai_personality, white_bot, black_bot,
            time_left=time_left, human_turn=human_turn
        )

        start_btn, quit_btn = draw_game_menu_buttons(screen, debug_rect)


        # if human_turn and not game_over:
        #     timer_text = timer_font.render(
        #         f"Time: {int(time_left)}s",
        #         True,
        #         p.Color("red") if time_left <= 5 else p.Color("black")
        #     )
        #     screen.blit(timer_text, (BOARD_WIDTH + 20, 20))

        p.display.flip()
        clock.tick(MAX_FPS)

if __name__ == "__main__":
    main()
