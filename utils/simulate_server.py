# 本地模拟 Server（推荐版）
import paho.mqtt.client as mqtt
from generated import robomaster_pb2 as rm_pb
import time

broker = mqtt.Client()
broker.connect("localhost", 1883, 60)

stage_list = [1, 2, 3, 4]
stage_idx = 0
red_score = 0

def simulate_game_status():
    global stage_idx, red_score

    gs = rm_pb.GameStatus()
    gs.current_stage = stage_list[stage_idx]
    gs.red_score = red_score
    gs.blue_score = red_score // 2
    gs.stage_countdown_sec = max(0, 300 - red_score * 5)
    gs.is_paused = False

    broker.publish("GameStatus", gs.SerializeToString())

    # 模拟状态变化
    red_score += 1
    stage_idx = (stage_idx + 1) % len(stage_list)

while True:
    simulate_game_status()
    time.sleep(1)
    def simulate_event():
        e = rm_pb.Event()
        e.event_id = 1001
        e.param = "Simulated Event"
        broker.publish("Event", e.SerializeToString())
