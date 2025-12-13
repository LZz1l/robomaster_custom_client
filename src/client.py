import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from generated import robomaster_pb2 as rm_pb
from config import SERVER_IP, MQTT_PORT, CLIENT_ID, RECONNECT_DELAY, LOG_FILE
import logging
import time
import cv2
import socket
import threading
import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image, ImageTk

# 日志设置
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

# 全局变量
game_stage = "Unknown"
red_score = 0
event_log = []  # 事件列表
video_frame = None  # 当前视频帧


# UI函数
def update_ui():
    root = tk.Tk()
    root.title("RoboMaster Client UI")

    # 状态面板
    status_frame = ttk.Frame(root)
    status_frame.pack(side=tk.LEFT, padx=10)
    ttk.Label(status_frame, text="Game Stage:").grid(row=0, column=0)
    stage_label = ttk.Label(status_frame, text=game_stage)
    stage_label.grid(row=0, column=1)
    ttk.Label(status_frame, text="Red Score:").grid(row=1, column=0)
    score_label = ttk.Label(status_frame, text=red_score)
    score_label.grid(row=1, column=1)

    # 视频嵌入
    video_canvas = tk.Canvas(root, width=640, height=480)
    video_canvas.pack(side=tk.LEFT, padx=10)

    # 交互面板
    interact_frame = ttk.Frame(root)
    interact_frame.pack(side=tk.RIGHT, padx=10)

    # 事件日志列表
    ttk.Label(interact_frame, text="Event Log:").pack()
    event_listbox = tk.Listbox(interact_frame, height=10, width=50)
    event_listbox.pack()

    # 输入框和按钮
    ttk.Label(interact_frame, text="Map Target X/Y:").pack()
    x_entry = ttk.Entry(interact_frame)
    x_entry.pack()
    y_entry = ttk.Entry(interact_frame)
    y_entry.pack()
    send_map_btn = ttk.Button(interact_frame, text="Send Map Target",
                              command=lambda: send_map_target(float(x_entry.get() or 0), float(y_entry.get() or 0)))
    send_map_btn.pack()

    send_rc_btn = ttk.Button(interact_frame, text="Send RemoteControl", command=lambda: send_remote_control(100, True))
    send_rc_btn.pack()

    def refresh():
        stage_label.config(text=game_stage)
        score_label.config(text=red_score)
        event_listbox.delete(0, tk.END)
        for event in event_log:
            event_listbox.insert(tk.END, event)

        # 更新视频
        global video_frame
        if video_frame is not None:
            try:
                img = Image.fromarray(cv2.cvtColor(video_frame, cv2.COLOR_BGR2RGB))
                imgtk = ImageTk.PhotoImage(image=img)
                video_canvas.imgtk = imgtk
                video_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            except Exception as e:
                logging.error(f"UI video update error: {e}")

        root.after(100, refresh)  # 每100ms刷新

    refresh()
    root.mainloop()


# MQTT回调
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("Connected successfully")
        logging.info("Connected to MQTT server")
        client.subscribe("GameStatus")
        client.subscribe("Event")
        client.subscribe("GlobalUnitStatus")
    else:
        print(f"Connection failed with code {reason_code}")
        logging.error(f"Connection failed with code {reason_code}")


def on_message(client, userdata, msg):
    global game_stage, red_score, event_log
    try:
        if msg.topic == "GameStatus":
            game_status = rm_pb.GameStatus()
            game_status.ParseFromString(msg.payload)
            game_stage = game_status.current_stage
            red_score = game_status.red_score
            print(f"Game stage: {game_stage}, Red score: {red_score}")
            logging.info(f"GameStatus received: stage {game_stage}")
        elif msg.topic == "Event":
            event = rm_pb.Event()
            event.ParseFromString(msg.payload)
            event_str = f"Event ID: {event.event_id}, Param: {event.param}"
            event_log.append(event_str)
            if len(event_log) > 10:
                event_log.pop(0)
            print(event_str)
            logging.info(event_str)
        # 添加其他处理
    except Exception as e:
        print(f"Parse error: {e}")
        logging.error(f"Parse error on topic {msg.topic}: {e}")


def on_disconnect(client, userdata, rc):
    print("Disconnected, trying to reconnect...")
    logging.warning("Disconnected, reconnecting...")
    time.sleep(RECONNECT_DELAY)
    client.reconnect()


# UDP视频接收（HEVC解码简化，实际需ffmpeg集成）
def receive_video():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 3334))
    while True:
        data, addr = sock.recvfrom(65535)
        try:
            global video_frame
            nparr = np.frombuffer(data, np.uint8)
            video_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            logging.info("Video frame received")
        except Exception as e:
            logging.error(f"Video decode error: {e}")


# 发送示例函数
def send_remote_control(mouse_x=100, left_down=True):
    rc = rm_pb.RemoteControl()
    rc.mouse_x = mouse_x
    rc.left_button_down = left_down
    payload = rc.SerializeToString()
    client.publish("RemoteControl", payload)
    logging.info("Sent RemoteControl")


def send_map_target(target_x=500, target_y=300):
    map_target = rm_pb.MapCommand()  # 假设proto有MapCommand，根据文档调整
    map_target.target_x = target_x
    map_target.target_y = target_y
    payload = map_target.SerializeToString()
    client.publish("MapCommand", payload)
    logging.info(f"Sent Map Target: ({target_x}, {target_y})")


client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

try:
    client.connect(SERVER_IP, MQTT_PORT, 60)
except Exception as e:
    print("Connection failed: ", e)
    logging.error(f"Connection failed: {e}")

client.loop_start()

# 启动线程
ui_thread = threading.Thread(target=update_ui)
ui_thread.start()
video_thread = threading.Thread(target=receive_video)
video_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    client.disconnect()
    ui_thread.join()
    video_thread.join()