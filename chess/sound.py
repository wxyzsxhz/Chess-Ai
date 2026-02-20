"""
Sound management for the chess game.
"""

import pygame as p

class SoundManager:
    def __init__(self):
        p.mixer.init()
        self.move_sound = p.mixer.Sound("sounds/move-sound.mp3")
        self.capture_sound = p.mixer.Sound("sounds/capture.mp3")
        self.promote_sound = p.mixer.Sound("sounds/promote.mp3")
    
    def play_move(self):
        self.move_sound.play()
    
    def play_capture(self):
        self.capture_sound.play()
    
    def play_promote(self):
        self.promote_sound.play()