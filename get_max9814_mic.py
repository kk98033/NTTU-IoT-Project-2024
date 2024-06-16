import pyaudio
import socket
import numpy as np
import queue
import argparse
import threading
import signal
import sys
import time

TCP_IP = "0.0.0.0"
TCP_PORT = 8888

def debug_message(message):
    print(f"[DEBUG] {message}")

def signal_handler(sig, frame):
    global running
    debug_message('You pressed Ctrl+C!')
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# 創建TCP服務器
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind((TCP_IP, TCP_PORT))
serversocket.listen(1)
serversocket.settimeout(1)  # 設定1秒的timeout以便能夠捕捉到Ctrl+C

debug_message(f"Server listening on {TCP_IP}:{TCP_PORT}")

# 初始化PyAudio
p = pyaudio.PyAudio()

# 找到虛擬音頻線的裝置索引
output_device_index = None
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    debug_message(f"Checking device {i}: {dev['name']}")
    if "CABLE Input" in dev['name']:  # 使用 "CABLE Input" 來匹配裝置名稱
        output_device_index = i
        debug_message(f"Found CABLE Input device at index {i}")
        break

if output_device_index is None:
    debug_message("找不到虛擬音頻線裝置")
    p.terminate()
    sys.exit(1)

# 使用 32 位元格式 (pyaudio.paInt32)
stream = p.open(format=32,  # 使用 32 位元格式
                channels=1,
                rate=8000,
                output=True,
                output_device_index=output_device_index)
debug_message("開始接收並播放音頻數據...")

# 參數解析
parser = argparse.ArgumentParser()
parser.add_argument("--chunk_size", type=int, default=1280, required=False)
parser.add_argument("--model_path", type=str, default="model/hey_Hikari.onnx", required=False)
parser.add_argument("--inference_framework", type=str, default='onnx', required=False)
args = parser.parse_args()

FORMAT = pyaudio.paInt32
CHANNELS = 1
RATE = 16000
CHUNK = args.chunk_size
audio = pyaudio.PyAudio()
mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
debug_message("Microphone stream opened")

# 音頻數據隊列
audio_queue = queue.Queue()

running = True

# 音頻讀取函數
def read_audio():
    global running
    global mic_stream
    while running:
        try:
            audio_data = np.frombuffer(mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.int32)
            audio_queue.put(audio_data)
            # debug_message("Audio data read and queued")  # 確認音頻數據被讀取並放入隊列
        except IOError as e:
            debug_message(f"IOError reading audio: {e}")
            debug_message("Microphone disconnected, attempting to reconnect...")
            while running:
                try:
                    mic_stream.close()  # 關閉當前的mic_stream
                    debug_message("Mic stream closed")
                    mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
                    debug_message("Microphone reconnected")
                    break
                except IOError as e:
                    debug_message(f"Error reconnecting microphone: {e}")
                    debug_message("Retrying in 5 seconds...")
                    time.sleep(5)
        except Exception as e:
            debug_message(f"Unexpected error in read_audio: {e}")
            time.sleep(5)


# 啟動音頻讀取線程
audio_thread = threading.Thread(target=read_audio)
audio_thread.daemon = True
audio_thread.start()
debug_message("Audio read thread started")

connection = None

timeout_counter = 0

try:
    while running:
        try:
            if connection is None:
                debug_message("Waiting for a new connection...")
                connection, client_address = serversocket.accept()
                debug_message(f"Connection accepted from {client_address}")
                connection.settimeout(1.0)  # 設定1秒的timeout
                timeout_counter = 0  # 重置超時計數器

            # 接收來自ESP32的音頻數據
            data = connection.recv(800)
            if not data:
                debug_message("接收到空數據，結束連接")
                connection.close()
                connection = None
                continue  # 繼續等待新的連接
            else:
                stream.write(data)
                debug_message("Received and played audio data")
                timeout_counter = 0  # 重置超時計數器
        except socket.timeout:
            timeout_counter += 1
            debug_message("Time out")
            if timeout_counter >= 5:  # 超時計數達到5秒鐘
                debug_message("Connection timed out for more than 5 seconds, closing connection")
                connection.close()
                connection = None
                timeout_counter = 0  # 重置超時計數器
            continue  # 忽略超時錯誤，繼續等待數據
        except ConnectionResetError:
            debug_message("Client disconnected abruptly")
            connection.close()
            connection = None
            continue  # 繼續等待新的連接
        except Exception as e:
            debug_message(f"Error receiving or writing data: {e}")
            if connection:
                connection.close()
                connection = None
except Exception as e:
    debug_message(f"Unexpected error: {e}")
finally:
    try:
        debug_message("Cleaning up resources...")
        if connection:
            connection.close()
        stream.stop_stream()
        stream.close()
        p.terminate()
        serversocket.close()
        debug_message("所有資源已清理")
    except Exception as e:
        debug_message(f"Error during cleanup: {e}")

debug_message("程式已結束")