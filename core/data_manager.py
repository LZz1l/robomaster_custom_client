# core/data_manager.py

from core.game_state import GameState
from core.event_state import EventState

class DataManager:
    def __init__(self):
        self.game = GameState()
        self.event = EventState()

    # ===== MQTT 入口 =====
    def on_game_status(self, msg):
        self.game.update_from_proto(msg)

    def on_event(self, event_str):
        self.event.add_event(event_str)
