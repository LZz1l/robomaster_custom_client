# core/event_state.py

class EventState:
    def __init__(self, max_len=10):
        self.events = []
        self.max_len = max_len

    def add_event(self, event_str):
        self.events.append(event_str)
        if len(self.events) > self.max_len:
            self.events.pop(0)
