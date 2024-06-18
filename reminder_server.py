from flask import Flask, request, jsonify
import threading
import requests
import time
import json
from datetime import datetime
import numpy as np
import paho.mqtt.client as mqtt
import os
import random
from openai import OpenAI
from dotenv import load_dotenv

from api_tools import call_assistant_api, call_tts_and_save, play_new_audio

# 加載 .env 文件
load_dotenv()

app = Flask(__name__)

mqtt_server = "34.168.176.224"
mqtt_topic = "XYZ"

reminders = []
reminder_messages = []
alarms = []
last_movement_time = time.time()

def play_music():
    print("Playing music...")
    response = requests.post('http://localhost:5000/switch_audio', json={'file': 'c1LjCbzUPTg', 'type': 'youtube'})
    print(response.status_code, response.text)

def set_reminder(message: str, delay: int) -> str:
    if message in reminder_messages:
        return f"提醒 '{message}' 已經存在。"
    
    def reminder():
        remind_user(f"Reminder: {message}")
        print(f"Reminder: {message}")
        if t in reminders:
            reminders.remove(t)
        if message in reminder_messages:
            reminder_messages.remove(message)
    
    t = threading.Timer(delay, reminder)
    t.start()
    reminders.append(t)

    reminder_messages.append(message)

    if delay < 60:
        time_str = f"{delay} 秒"
    elif delay < 3600:
        time_str = f"{delay // 60} 分鐘"
    else:
        time_str = f"{delay // 3600} 小時"
    
    # remind_user(f"已設置提醒，將在 {time_str} 後提醒您: {message}")
    return f"已設置提醒，將在 {time_str} 後提醒您: {message}"


def set_alarm(time_to_ring: int) -> str:
    def alarm():
        play_music()
        if t in alarms:
            alarms.remove(t)
    
    t = threading.Timer(time_to_ring, alarm)
    t.start()
    alarms.append(t)

    if time_to_ring < 60:
        time_str = f"{time_to_ring} 秒"
    elif time_to_ring < 3600:
        time_str = f"{time_to_ring // 60} 分鐘"
    else:
        time_str = f"{time_to_ring // 3600} 小時"
    
    # remind_user(f"已設置鬧鐘，將在 {time_str} 後響鈴。")
    return f"已設置鬧鐘，將在 {time_str} 後響鈴。"

def set_alarm_at(month: int, day: int, hour: int, minute: int) -> str:
    now = datetime.now()
    alarm_time = datetime(now.year, month, day, hour, minute)
    delay = (alarm_time - now).total_seconds()

    if delay <= 0:
        # remind_user("指定的時間已過，無法設置鬧鐘。")
        return "指定的時間已過，無法設置鬧鐘。"

    if delay < 60:
        time_str = f"{delay} 秒"
    elif delay < 3600:
        time_str = f"{delay // 60} 分鐘"
    else:
        time_str = f"{delay // 3600} 小時"

    # remind_user(f"已設置鬧鐘，將在 {time_str} 後響鈴。")
    return set_alarm(int(delay))

# def update_movement(aX: int, aY: int, aZ: int, gX: int, gY: int, gZ: int):
#     global last_movement_time
#     threshold = 500
#     gravity = 9.8 * 1000  # 假設加速度值是以 milli-g 為單位

#     # 計算總加速度
#     total_acc = np.sqrt(aX**2 + aY**2 + aZ**2)
    
#     # 判斷是否有顯著的Z軸加速度變化
#     if abs(aZ) > threshold:
#         if abs(total_acc - gravity) < threshold:
#             print("The user is standing.")
#         else:
#             print("The user is sitting.")
#         last_movement_time = time.time()
#     else:
#         print("No significant movement detected.")
        
# def check_sedentary():
#     global last_movement_time
#     while True:
#         if time.time() - last_movement_time > 300:
#             remind_user_preconfigured("久坐提醒")
#             last_movement_time = time.time()
#         time.sleep(10)

def set_drink_water_reminder():
    while True:
        remind_user_preconfigured("喝水提醒")
        time.sleep(1200) # debug

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(mqtt_topic)

# 全局變量
ax_offset = 0
ay_offset = 0
az_offset = 0
gx_offset = 0
gy_offset = 0
gz_offset = 0
calibrated = False
last_movement_time = time.time()

def on_message(client, userdata, msg):
    global ax_offset, ay_offset, az_offset, gx_offset, gy_offset, gz_offset, calibrated
    data = json.loads(msg.payload.decode())
    aX = data.get('ax')
    aY = data.get('ay')
    aZ = data.get('az')
    gX = data.get('gx')
    gY = data.get('gy')
    gZ = data.get('gz')

    if all(v is not None for v in [aX, aY, aZ, gX, gY, gZ]):
        if not calibrated:
            calibrate_sensor(aX, aY, aZ, gX, gY, gZ)
        else:
            update_movement(aX, aY, aZ, gX, gY, gZ)
    else:
        print("Some values are None, check your JSON keys.")

def calibrate_sensor(aX, aY, aZ, gX, gY, gZ, samples=10):
    global ax_offset, ay_offset, az_offset, gx_offset, gy_offset, gz_offset, calibrated
    if not hasattr(calibrate_sensor, "count"):
        calibrate_sensor.count = 0
        calibrate_sensor.ax_sum = 0
        calibrate_sensor.ay_sum = 0
        calibrate_sensor.az_sum = 0
        calibrate_sensor.gx_sum = 0
        calibrate_sensor.gy_sum = 0
        calibrate_sensor.gz_sum = 0

    calibrate_sensor.ax_sum += aX
    calibrate_sensor.ay_sum += aY
    calibrate_sensor.az_sum += aZ
    calibrate_sensor.gx_sum += gX
    calibrate_sensor.gy_sum += gY
    calibrate_sensor.gz_sum += gZ
    calibrate_sensor.count += 1

    if calibrate_sensor.count >= samples:
        ax_offset = calibrate_sensor.ax_sum / samples
        ay_offset = calibrate_sensor.ay_sum / samples
        az_offset = (calibrate_sensor.az_sum / samples) - 9800  # 假設 9800 mg 為 1g
        gx_offset = calibrate_sensor.gx_sum / samples
        gy_offset = calibrate_sensor.gy_sum / samples
        gz_offset = calibrate_sensor.gz_sum / samples
        calibrated = True
        print("Calibration completed")
        print(f"Offsets - Ax: {ax_offset}, Ay: {ay_offset}, Az: {az_offset}, Gx: {gx_offset}, Gy: {gy_offset}, Gz: {gz_offset}")

def calculate_tilt_angles(aX, aY, aZ):
    pitch = np.arctan2(aY, np.sqrt(aX**2 + aZ**2)) * 180 / np.pi
    roll = np.arctan2(aX, np.sqrt(aY**2 + aZ**2)) * 180 / np.pi
    return pitch, roll

def update_movement(aX: int, aY: int, aZ: int, gX: int, gY: int, gZ: int):
    global last_movement_time
    threshold = 1000  # 調整閾值
    gravity = 9.8 * 1000  # 假設加速度值是以 milli-g 為單位
    gyro_threshold = 500  # 陀螺儀閾值

    # 應用校準偏移值
    aX -= ax_offset
    aY -= ay_offset
    aZ -= az_offset
    gX -= gx_offset
    gY -= gy_offset
    gZ -= gz_offset

    # 計算總加速度
    total_acc = np.sqrt(aX**2 + aY**2 + aZ**2)
    
    # 計算俯仰角和滾轉角
    pitch, roll = calculate_tilt_angles(aX, aY, aZ)

    # 打印校準後的數據和總加速度
    print(f"Calibrated Ax: {aX}, Ay: {aY}, Az: {aZ}, Total Acc: {total_acc}")
    print(f"Calibrated Gx: {gX}, Gy: {gY}, Gz: {gZ}")
    print(f"Pitch: {pitch}, Roll: {roll}")

    # 判斷是否有顯著的Z軸加速度變化
    if abs(total_acc - gravity) < threshold:
        if abs(gX) < gyro_threshold and abs(gY) < gyro_threshold and abs(gZ) < gyro_threshold:
            print(last_movement_time)
            if abs(aZ - gravity) < threshold:
                print("The device is stationary.")
            else:
                if pitch > 10 or roll > 10:  # 根據角度判斷是否站立
                    print("The user is standing.")
                    last_movement_time = time.time()
                elif 0 < pitch <= 10 or 0 < roll <= 10:  # 根據角度判斷是否坐下
                    print("The user is sitting.")
                else:
                    print("The user is moving.")
                    print()
                    print("[TIME]", time.time() - last_movement_time, time.time(), last_movement_time)
                    print()
                    last_movement_time = time.time()

        else:
            print("The user is moving.")
            last_movement_time = time.time()
    else:
        print("No significant movement detected.")

def check_sedentary():
    global last_movement_time
    while True:
        print("[TIME]", time.time() - last_movement_time, time.time(), last_movement_time)
        if time.time() - last_movement_time > 300: # debug
            remind_user_preconfigured("久坐提醒")
            last_movement_time = time.time()
        time.sleep(10)

def choose_random_reminder(remind_text):
    print(remind_text)
    reminders = {
        '久坐提醒': [
            "久坐提醒-1.mp3",
            "久坐提醒-2.mp3",
            "久坐提醒-3.mp3",
            "久坐提醒-4.mp3",
            "久坐提醒-5.mp3",
            "久坐提醒-6.mp3"
        ],
        '喝水提醒': [
            "喝水提醒-1.mp3",
            "喝水提醒-2.mp3",
            "喝水提醒-3.mp3",
            "喝水提醒-4.mp3",
            "喝水提醒-5.mp3"
        ]
    }
    
    if remind_text in reminders:
        return random.choice(reminders[remind_text])
    else:
        return "未知的提醒類型。"

def remind_user(remind_text):
    print('remind user: ', remind_text)
    if "喝水提醒" in remind_text or '久坐提醒' in remind_text:
        remind_user_preconfigured(remind_text)

    # client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # thread = client.beta.threads.create()
    # thread_id = thread.id

    # formatted_text = f"用你的話講(繁體中文)：{remind_text}，兇一點"
    # assistant_response = call_assistant_api(formatted_text, thread_id)
    # if not assistant_response:
    #     print('Failed to get assistant response')
    #     return

    # call_tts_and_save(assistant_response, 'reminder_speech.mp3')
    return

def remind_user_preconfigured(remind_text):
    print('remind text: ', remind_text)
    if "喝水提醒" in remind_text:
        remind_path = 'Preconfigured_Audio_Storage/' + choose_random_reminder("喝水提醒")
    if '久坐提醒' in remind_text:
        remind_path = 'Preconfigured_Audio_Storage/' + choose_random_reminder('久坐提醒')
    print(f'播放隨機語音: {remind_path}')
    play_new_audio(remind_path)
    return

sedentary_thread = threading.Thread(target=check_sedentary, daemon=True)
sedentary_thread.start()

drink_water_thread = threading.Thread(target=set_drink_water_reminder, daemon=True)
drink_water_thread.start()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_server, 1883, 60)

mqtt_thread = threading.Thread(target=client.loop_forever, daemon=True)
mqtt_thread.start()

@app.route('/set_reminder', methods=['POST'])
def api_set_reminder():
    data = request.json
    message = data.get('message')
    delay = data.get('delay')
    response = set_reminder(message, delay)
    return jsonify({"status": "success", "message": response})

@app.route('/set_alarm', methods=['POST'])
def api_set_alarm():
    data = request.json
    time_to_ring = data.get('time_to_ring')
    response = set_alarm(time_to_ring)
    return jsonify({"status": "success", "message": response})

@app.route('/set_alarm_at', methods=['POST'])
def api_set_alarm_at():
    data = request.json
    month = data.get('month')
    day = data.get('day')
    hour = data.get('hour')
    minute = data.get('minute')
    response = set_alarm_at(month, day, hour, minute)
    return jsonify({"status": "success", "message": response})

@app.route('/list_reminders', methods=['GET'])
def list_reminders():
    return jsonify({"status": "success", "reminders": reminder_messages})

if __name__ == '__main__':
    # response = set_reminder('去上課', 20)
    # print(response)

    response = set_alarm(10)
    # print(response)

    # response = set_alarm_at(6, 14, 13, 0)
    # print(response)

    app.run(port=6669)
