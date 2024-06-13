import os
import pyaudio
import numpy as np
import webrtcvad
import noisereduce as nr
from openai import OpenAI
import openwakeword
from openwakeword.model import Model
import argparse
import threading
import queue
import time
import requests
from dotenv import load_dotenv
import wave
from pathlib import Path

from assistant_api_not_streaming import send_message_to_assistant

# 加載 .env 文件
load_dotenv()

# 從環境變數中取得 API 金鑰
api_key = os.getenv('OPENAI_API_KEY')

# 檢查是否成功加載 API 金鑰
if not api_key:
    raise ValueError("API key not found. Make sure to set OPENAI_API_KEY in your .env file")

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# assistant setting
assistant_id = "asst_CAnTShQDTVvObtJyPbNB04UP"
thread = client.beta.threads.create()
thread_id = thread.id  # 取得新創建的 thread 的 ID

# Parse input arguments
parser = argparse.ArgumentParser()
parser.add_argument("--chunk_size", type=int, default=1280, required=False)
parser.add_argument("--model_path", type=str, default="model/hey_Hikari.onnx", required=False)
parser.add_argument("--inference_framework", type=str, default='onnx', required=False)
args = parser.parse_args()

# Get microphone stream
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = int(RATE * 0.03)  # 30ms 的幀大小
audio = pyaudio.PyAudio()
mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

# Load pre-trained openwakeword models
owwModel = Model(wakeword_models=[args.model_path], inference_framework=args.inference_framework)

# Queue for audio data
audio_queue = queue.Queue()

# Function to read from the microphone
def read_audio():
    while True:
        audio_data = np.frombuffer(mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        audio_queue.put(audio_data)

# Start the audio reading thread
audio_thread = threading.Thread(target=read_audio)
audio_thread.daemon = True
audio_thread.start()

# Function to save data to file
def save_to_wav(filename, audio_data):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(audio_data.tobytes())
    wf.close()

def beep():
    url = 'http://127.0.0.1:1880/beep'
    data = {
        'beep': '1',
    }

    print('準備呼叫 Node-RED API...')

    try:
        response = requests.post(url, json=data, timeout=10)  # 設定超時為 10 秒
        print('API 請求已發送...')
    except requests.Timeout:
        print('呼叫 API 超時。請確認 Node-RED 伺服器是否在運行。')
        return
    except requests.ConnectionError:
        print('無法連接到 Node-RED 伺服器。請檢查伺服器是否在運行，以及網路設置是否正確。')
        return
    except Exception as e:
        print('呼叫 API 時出現未知錯誤:', e)
        return

    # 處理回應
    if response.status_code == 200:
        try:
            result = response.json()
            print('Result:', result)
        except ValueError:
            print('回應不是 JSON 格式:', response.text)
    else:
        print('Failed to call Node-RED API:', response.status_code)
    return

# Function to send data to OpenAI STT API
def send_data_to_openai_stt(audio_file):
    try:
        with open(audio_file, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            print("Transcription:", transcription.text)
            return transcription.text
    except Exception as e:
        print(f"Error occurred: {e}")

def call_assistant_api(user_message):
    return send_message_to_assistant(assistant_id, thread_id, user_message)

def call_tts_and_save(text, save_path):
    uri = f"http://127.0.0.1:9880/?text={text}&text_language=zh"
    stream_audio_from_api(uri, save_path)

def stream_audio_from_api(uri, save_path):
    try:
        print('streaming')
        response = requests.get(uri, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(save_path, 'wb') as audio_file:
            for chunk in response.iter_content(chunk_size=8192):
                audio_file.write(chunk)
        
        print(f"Audio saved to {save_path}")
        play_new_audio()
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"General error: {e}")

def process_user_audio_response():
    stt = send_data_to_openai_stt('recorded_audio.wav')
    if not stt:
        print('Failed to get stt')
        return
    
    assistant_response = call_assistant_api(stt)
    if not assistant_response:
        print('Failed to get assistant response')
        return

    call_tts_and_save(assistant_response, 'speech.mp3')

def play_new_audio():
    response = requests.post('http://localhost:5000/switch_audio', json={'file': 'speech.mp3'})
    print(response.status_code, response.text)

# 初始化 WebRTC VAD
vad = webrtcvad.Vad()
vad.set_mode(3)  # 0, 1, 2, 3 依次增強人聲檢測的靈敏度

print("Listening for wakewords...")

recording = False
recorded_audio = []
silence_threshold = 15000  # Adjust this threshold based on your needs
silence_duration = 1.5  # Duration of silence in seconds to stop recording
silence_start = None

try:
    while True:
        if not audio_queue.empty():
            audio_data = audio_queue.get()
            audio_level = np.abs(audio_data).mean()

            # 降噪處理
            reduced_noise = nr.reduce_noise(y=audio_data, sr=RATE)

            if recording:
                recorded_audio.append(reduced_noise)
                if audio_level < silence_threshold:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > silence_duration:
                        recording = False
                        audio_data_concat = np.concatenate(recorded_audio)
                        save_to_wav('recorded_audio.wav', audio_data_concat)
                        print("Audio saved to 'recorded_audio.wav'")
                        
                        process_user_audio_response()

                        recorded_audio = []
                        silence_start = None
                else:
                    silence_start = None

            prediction = owwModel.predict(audio_data)
            for mdl in owwModel.prediction_buffer.keys():
                scores = list(owwModel.prediction_buffer[mdl])
                if scores[-1] > 0.5:
                    recording = True
                    print('beep')
                    beep()
                    recorded_audio = [reduced_noise]  # Start a new recording
                    print("Wakeword detected! Start recording...")

            print(f"Audio level: {audio_level} (recording: {recording})", end='\r')

except KeyboardInterrupt:
    print("Recording and Playing stopped")

finally:
    # 關閉音訊流
    mic_stream.stop_stream()
    mic_stream.close()
    audio.terminate()
