#本地模拟Server测试
import paho.mqtt.client as mqtt
from generated import robomaster_pb2 as rm_pb
import time

broker = mqtt.Client()
broker.connect("localhost", 1883, 60)  # 本地broker测试

def simulate_game_status():
    gs = rm_pb.GameStatus()
    gs.current_stage = 4
    payload = gs.SerializeToString()
    broker.publish("GameStatus", payload)

while True:
    simulate_game_status()
    time.sleep(1)