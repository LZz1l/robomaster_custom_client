# core/game_state.py

class GameState:
    def __init__(self):
        self.stage = "Unknown"
        self.red_score = 0

    def update_from_proto(self, msg):
        self.stage = msg.current_stage
        self.red_score = msg.red_score
