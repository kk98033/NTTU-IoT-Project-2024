import threading
import time
import json
from datetime import datetime
import paho.mqtt.client as mqtt

# MQTT server
mqtt_server = "34.168.176.224"
mqtt_topic = "xyz"

reminders = []
alarms = []
last_movement_time = time.time()

def play_music():
    # 假設這是播放音樂的函數，你可以自行實現
    print("Playing music...")

def set_reminder(message: str, delay: int) -> str:
    """
    設置提醒。

    參數:
    message (str): 提醒的內容。
    delay (int): 延遲時間，以秒為單位。

    返回:
    str: 設置提醒的說明字串。
    """
    def reminder():
        print(f"Reminder: {message}")
        print('debug', reminders)
        if t in reminders:
            reminders.remove(t)
    
    t = threading.Timer(delay, reminder)
    t.start()
    reminders.append(t)

    # 判斷時間單位並生成說明字串
    if delay < 60:
        time_str = f"{delay} 秒"
    elif delay < 3600:
        time_str = f"{delay // 60} 分鐘"
    else:
        time_str = f"{delay // 3600} 小時"
    
    return f"已設置提醒，將在 {time_str} 後提醒您: {message}"

def set_alarm(time_to_ring: int) -> str:
    """
    設置鬧鐘。

    參數:
    time_to_ring (int): 延遲時間，以秒為單位。

    返回:
    str: 設置鬧鐘的說明字串。
    """
    def alarm():
        play_music()
        if t in alarms:
            alarms.remove(t)
    
    t = threading.Timer(time_to_ring, alarm)
    t.start()
    alarms.append(t)

    # 判斷時間單位並生成說明字串
    if time_to_ring < 60:
        time_str = f"{time_to_ring} 秒"
    elif time_to_ring < 3600:
        time_str = f"{time_to_ring // 60} 分鐘"
    else:
        time_str = f"{time_to_ring // 3600} 小時"
    
    return f"已設置鬧鐘，將在 {time_str} 後響鈴。"

def set_alarm_at(month: int, day: int, hour: int, minute: int) -> str:
    """
    設置指定日期和時間的鬧鐘。

    參數:
    month (int): 月份 (1-12)。
    day (int): 日期 (1-31)。
    hour (int): 小時 (0-23)。
    minute (int): 分鐘 (0-59)。

    返回:
    str: 設置鬧鐘的說明字串。
    """
    now = datetime.now()
    alarm_time = datetime(now.year, month, day, hour, minute)
    delay = (alarm_time - now).total_seconds()

    if delay <= 0:
        return "指定的時間已過，無法設置鬧鐘。"

    return set_alarm(int(delay))

def list_reminders():
    """
    列出所有當前活動的提醒。

    返回:
    list: 包含所有提醒的信息和剩餘時間的列表。
    """
    return [{"message": t.function.__closure__[0].cell_contents, "time_left": t.interval - (time.time() - t.finished_time)} for t in reminders]

def list_alarms():
    """
    列出所有當前活動的鬧鐘。

    返回:
    list: 包含所有鬧鐘的剩餘時間的列表。
    """
    return [{"time_left": t.interval - (time.time() - t.finished_time)} for t in alarms]
[{"message": t.function.__closure__[0].cell_contents, "time_left": t.interval - (time.time() - t.finished_time)} for t in reminders]

def update_movement(aX: int, aY: int, aZ: int, gX: int, gY: int, gZ: int):
    """
    更新用戶的活動狀態。

    參數:
    aX, aY, aZ (int): 加速度計數據。
    gX, gY, gZ (int): 陀螺儀數據。
    """
    global last_movement_time
    threshold = 500  # 自定義閾值，可以根據實際情況調整

    if abs(aX) > threshold or abs(aY) > threshold or abs(aZ) > threshold or \
       abs(gX) > threshold or abs(gY) > threshold or abs(gZ) > threshold:
        last_movement_time = time.time()

def check_sedentary():
    """
    檢查用戶是否久坐超過5分鐘，並觸發久坐提醒。
    """
    global last_movement_time
    while True:
        if time.time() - last_movement_time > 300:  # 300秒 = 5分鐘
            set_reminder("久坐提醒：起來活動一下！", 0)
            last_movement_time = time.time()  # 重置時間以避免連續觸發
        time.sleep(10)  # 每10秒檢查一次


def set_drink_water_reminder():
    """
    設置每20分鐘提醒一次喝水。
    """
    while True:
        set_reminder("喝水提醒：記得喝水喔！", 0)
        time.sleep(1200)  # 1200秒 = 20分鐘

def on_connect(client, userdata, flags, rc):
    """
    當連接到MQTT服務器時調用的回調函數。
    """
    print("Connected with result code " + str(rc))
    client.subscribe(mqtt_topic)

def on_message(client, userdata, msg):
    """
    當接收到來自MQTT服務器的消息時調用的回調函數。
    """
    data = json.loads(msg.payload.decode())
    aX = data.get('aX')
    aY = data.get('aY')
    aZ = data.get('aZ')
    gX = data.get('gX')
    gY = data.get('gY')
    gZ = data.get('gZ')
    print(data)
    update_movement(aX, aY, aZ, gX, gY, gZ)

# 啟動久坐檢查線程
sedentary_thread = threading.Thread(target=check_sedentary, daemon=True)
sedentary_thread.start()

# 啟動喝水提醒線程
drink_water_thread = threading.Thread(target=set_drink_water_reminder, daemon=True)
drink_water_thread.start()

# 配置MQTT客戶端並連接到服務器
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_server, 1883, 60)

# 啟動MQTT客戶端的循環
mqtt_thread = threading.Thread(target=client.loop_forever, daemon=True)
mqtt_thread.start()

if __name__ == '__main__':
    response = set_reminder('hello workd', 10)
    print(response)

    response = set_alarm(300)  # 300秒 = 5分鐘
    print(response)

    response = set_alarm_at(6, 14, 13, 0)  # 6月14日下午1:00
    print(response)

    while True:
        msg = input()
        if msg == 'exit':
            break