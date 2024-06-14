import time
import json
import random
import paho.mqtt.client as mqtt

# MQTT server
mqtt_server = "34.168.176.224"
mqtt_topic = "xyz"

def generate_random_data():
    """
    生成隨機但合理的陀螺儀和加速度計數據。
    """
    data = {
        "aX": random.randint(-1000, 1000),
        "aY": random.randint(-1000, 1000),
        "aZ": random.randint(16000, 17000),
        "gX": random.randint(-500, 500),
        "gY": random.randint(-500, 500),
        "gZ": random.randint(-500, 500)
    }
    return data

def on_connect(client, userdata, flags, rc):
    """
    當連接到MQTT服務器時調用的回調函數。
    """
    print("Connected with result code " + str(rc))

def send_random_data():
    """
    每10秒發送一次隨機生成的數據。
    """
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(mqtt_server, 1883, 60)
    
    client.loop_start()
    while True:
        data = generate_random_data()
        client.publish(mqtt_topic, json.dumps(data))
        print(f"Sent data: {data}")
        time.sleep(10)

if __name__ == "__main__":
    send_random_data()
