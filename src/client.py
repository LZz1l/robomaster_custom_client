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

# ===== 新增：数据管理层 =====
from core.data_manager import DataManager

# 日志设置
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# ===== 全局唯一数据中心 =====
data_manager = DataManager()

# 视频帧（下一阶段再纳入 DataManager）
video_frame = None


# ================= UI =================
def update_ui():
    root = tk.Tk()
    root.title("RoboMaster Custom Client")

    # 状态面板
    status_frame = ttk.Frame(root)
    status_frame.pack(side=tk.LEFT, padx=10)

    ttk.Label(status_frame, text="Game Stage:").grid(row=0, column=0)
    stage_label = ttk.Label(status_frame, text="Unknown")
    stage_label.grid(row=0, column=1)

    ttk.Label(status_frame, text="Red Score:").grid(row=1, column=0)
    score_label = ttk.Label(status_frame, text="0")
    score_label.grid(row=1, column=1)

    # 视频区域
    video_canvas = tk.Canvas(root, width=640, height=480)
    video_canvas.pack(side=tk.LEFT, padx=10)

    # 交互面板
    interact_frame = ttk.Frame(root)
    interact_frame.pack(side=tk.RIGHT, padx=10)

    ttk.Label(interact_frame, text="Event Log:").pack()
    event_listbox = tk.Listbox(interact_frame, height=10, width=50)
    event_listbox.pack()

    ttk.Label(interact_frame, text="Map Target X/Y:").pack()
    x_entry = ttk.Entry(interact_frame)
    x_entry.pack()
    y_entry = ttk.Entry(interact_frame)
    y_entry.pack()

    ttk.Button(
        interact_frame,
        text="Send Map Target",
        command=lambda: send_map_target(
            float(x_entry.get() or 0),
            float(y_entry.get() or 0)
        )
    ).pack()

    ttk.Button(
        interact_frame,
        text="Send RemoteControl",
        command=lambda: send_remote_control(100, True)
    ).pack()

    def refresh():
        # ===== 从 DataManager 读数据 =====
        stage_label.config(text=data_manager.game.stage)
        score_label.config(text=data_manager.game.red_score)

        event_listbox.delete(0, tk.END)
        for event in data_manager.event.events:
            event_listbox.insert(tk.END, event)

        # 更新视频
        global video_frame
        if video_frame is not None:
            try:
                img = Image.fromarray(
                    cv2.cvtColor(video_frame, cv2.COLOR_BGR2RGB)
                )
                imgtk = ImageTk.PhotoImage(image=img)
                video_canvas.imgtk = imgtk
                video_canvas.create_image(
                    0, 0, anchor=tk.NW, image=imgtk
                )
            except Exception as e:
                logging.error(f"UI video update error: {e}")

        root.after(100, refresh)

    refresh()
    root.mainloop()


# ================= MQTT =================
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        logging.info("Connected to MQTT server")
        client.subscribe("GameStatus")
        client.subscribe("Event")
        client.subscribe("GlobalUnitStatus")
    else:
        logging.error(f"Connection failed with code {reason_code}")


def on_message(client, userdata, msg):
    try:
        if msg.topic == "GameStatus":
            game_status = rm_pb.GameStatus()
            game_status.ParseFromString(msg.payload)

            # ===== 丢给 DataManager =====
            data_manager.on_game_status(game_status)

            logging.info(
                f"GameStatus: stage={game_status.current_stage}, "
                f"red_score={game_status.red_score}"
            )

        elif msg.topic == "Event":
            event = rm_pb.Event()
            event.ParseFromString(msg.payload)

            event_str = f"Event ID: {event.event_id}, Param: {event.param}"
            data_manager.on_event(event_str)

            logging.info(event_str)

    except Exception as e:
        logging.error(f"Parse error on topic {msg.topic}: {e}")


def on_disconnect(client, userdata, rc):
    logging.warning("Disconnected, reconnecting...")
    time.sleep(RECONNECT_DELAY)
    client.reconnect()


# ================= 视频 =================
def receive_video():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 3334))

    global video_frame
    while True:
        data, _ = sock.recvfrom(65535)
        try:
            nparr = np.frombuffer(data, np.uint8)
            video_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            logging.error(f"Video decode error: {e}")


# ================= 发送控制 =================
def send_remote_control(mouse_x=100, left_down=True):
    rc = rm_pb.RemoteControl()
    rc.mouse_x = mouse_x
    rc.left_button_down = left_down
    client.publish("RemoteControl", rc.SerializeToString())
    logging.info("Sent RemoteControl")


def send_map_target(target_x=500, target_y=300):
    map_cmd = rm_pb.MapCommand()
    map_cmd.target_x = target_x
    map_cmd.target_y = target_y
    client.publish("MapCommand", map_cmd.SerializeToString())
    logging.info(f"Sent Map Target: ({target_x}, {target_y})")


# ================= 启动 =================
client = mqtt.Client(
    callback_api_version=CallbackAPIVersion.VERSION2,
    client_id=CLIENT_ID
)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

try:
    client.connect(SERVER_IP, MQTT_PORT, 60)
except Exception as e:
    logging.error(f"Connection failed: {e}")

client.loop_start()

threading.Thread(target=update_ui, daemon=True).start()
threading.Thread(target=receive_video, daemon=True).start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    client.disconnect()
