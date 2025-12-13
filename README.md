# RoboMaster Custom Client

## 项目概述
这个项目是一个基于Python的RoboMaster自定义客户端，用于连接RoboMaster Server（赛事引擎），通过MQTT协议发送/接收Protobuf数据，支持小地图交互、远程控制、图形绘制等功能（基于2026高校系列赛通信协议）。此外，集成UDP视频流接收（端口3334）和tkinter图形UI显示状态/日志/交互按钮。适用于RoboMaster比赛开发测试或模拟。

项目路径：C:\Users\ASUS\OneDrive\Desktop\robomaster_custom_client

**关键功能**：
- MQTT连接Server，订阅GameStatus/Event等，发送RemoteControl/MapTarget等指令。
- UDP接收视频流，并嵌入UI显示。
- tkinter UI：显示游戏状态、事件日志、视频帧，支持输入发送小地图目标、按钮发送控制指令。
- 日志记录到logs/client.log。
- 模拟模式（无Server时测试Protobuf逻辑）。

**注意**：当前使用Student版Engine可能不支持MQTT（连接失败）。建议联系DJI获取完整版Engine。

## 系统要求
- Python 3.8+（推荐3.11）。
- Windows（已测试）。
- 依赖库：paho-mqtt, protobuf, opencv-python, pillow（PIL）。
- Protobuf编译器（protoc）：从https://github.com/protocolbuffers/protobuf/releases下载。
- RoboMaster Engine/Server（完整版，IP 192.168.12.1:3333）。
- 可选：硬件串口（COM线）用于备用串口模式。

## 安装步骤
1. **安装依赖**：
   ```
   pip install paho-mqtt protobuf opencv-python pillow pyserial
   ```

2. **生成Protobuf类**：
   - 下载protoc.exe（Windows版），放在项目根目录。
   - cmd切换到项目路径：`cd C:\Users\ASUS\OneDrive\Desktop\robomaster_custom_client`
   - 运行：`protoc --python_out=generated proto/robomaster.proto`
   - 生成generated/robomaster_pb2.py。

3. **配置**：
   - 编辑config.py：调整SERVER_IP ("192.168.12.1")、MQTT_PORT (3333)，如Engine不同。
   - 创建logs/文件夹（日志保存）。

## 运行指南
1. **启动RoboMaster Engine**：
   - 运行RoboMasterEngine.exe（设置主IP 192.168.1.2，添加辅IP 192.168.12.1）。
   - 启动模拟比赛（1v1/3v3）。

2. **运行客户端**：
   - cmd：`python src/client.py`
   - 预期：尝试连接MQTT，打开tkinter UI窗口和视频显示。
   - 如果连接失败：打印"Connection failed"，进入模拟模式（控制台输出测试数据）。

3. **UI交互**：
   - 状态显示：Game Stage和Red Score实时更新。
   - 事件日志：列表显示接收的Event（ID和Param）。
   - 视频：嵌入窗口显示UDP流（如果有数据，按'q'关闭窗口）。
   - 输入/按钮：输入X/Y发送小地图目标；点击按钮发送RemoteControl。

4. **备用串口模式**（如果有硬件）：
   - 编辑src/serial_client.py COM_PORT ('COM3')。
   - 运行：`python src/serial_client.py`
   - 发送/接收串口协议数据。

## 测试步骤（给测试人员）
1. **准备**：
   - 确保Engine运行，网络连通（ping 192.168.12.1成功）。
   - 检查netstat端口3333/3334是否监听（PowerShell: `netstat -an | Select-String "3333"`）。

2. **基本连接测试**：
   - 运行client.py。
   - 检查控制台："Connected successfully"（成功）或"Connection failed"（失败，检查Engine/IP）。
   - UI打开：验证状态标签更新（如果Engine模拟比赛，Game Stage应变4）。

3. **交互测试**：
   - 输入X=500, Y=300，点击"Send Map Target"：检查日志"Sent Map Target"，Engine是否响应。
   - 点击"Send RemoteControl"：发送鼠标控制，日志记录。
   - 事件日志：如果Engine发送Event，列表更新。

4. **视频测试**：
   - Engine发送视频流：UI嵌入显示帧（如果无，检查UDP端口）。
   - 测试关闭：按'q'关闭视频窗口。

5. **模拟模式测试**：
   - 如果MQTT失败：控制台打印模拟发送/接收（e.g., "Simulated send: hex"）。
   - 运行utils/simulate_server.py（本地broker），改config.py IP="localhost"端口1883，再跑client.py测试订阅。

6. **日志检查**：
   - 运行后查看logs/client.log：记录连接/发送/错误。
   - 验证无解析错误。

7. **异常测试**：
   - 断网：检查自动重连（on_disconnect）。
   - 无效输入：UI发送按钮处理（e.g., 非数X/Y报错）。

8. **串口测试（如果硬件准备）**：
   - 连接COM线到主控模块。
   - 运行serial_client.py：检查发送协议帧，接收打印。

## 常见问题调试
- **MQTT连接失败**：Engine Student版不支持，联系DJI获取full version。检查IP/端口/防火墙。
- **Protobuf错误**：重新生成robomaster_pb2.py，确保proto文件完整。
- **视频无显示**：Engine未发送流，或端口错。检查opencv安装。
- **UI不更新**：检查线程（ui_thread/video_thread）。
- **Engine获取**：论坛bbs.robomaster.com问“RoboMaster Engine full version 2025 download”，或DJI支持。

## 贡献/联系
- 项目基于RoboMaster 2026协议开发。
- 测试反馈：报告bug到[您的邮箱/Issue]。
- 更新：如果Engine获取成功，测试MQTT功能。