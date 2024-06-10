import os
import pyaudio
import numpy as np
from openai import OpenAI
import openwakeword
from openwakeword.model import Model
import argparse
import threading
import queue
import time
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
CHUNK = args.chunk_size
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

# Function to send data to OpenAI STT API
def send_data_to_openai_stt(audio_file):
    # client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
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


def send_data_to_openai_tts(text):
    try:
        # client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )
        speech_file_path = Path(__file__).parent / "speech.mp3"
        response.stream_to_file(speech_file_path)
        # with open(speech_file_path, 'wb') as f:
        #     f.write(response['audio_content'])
        print(f"Speech saved to {speech_file_path}")
    except Exception as e:
        print(f"Error occurred: {e}")

def process_user_audio_response():
    stt = send_data_to_openai_stt('recorded_audio.wav')
    if not stt:
        print('Failed to get stt')
        return
    
    assistant_response = call_assistant_api(stt)
    if not assistant_response:
        print('Failed to get assistant response')
        return

    send_data_to_openai_tts(assistant_response)
    return

# Run capture loop continuously, checking for wakewords
if __name__ == "__main__":
    print("\n\n")
    print("#" * 100)
    print("Listening for wakewords...")
    print("#" * 100)
    print("\n")

    recording = False
    recorded_audio = []
    silence_threshold = 500  # Adjust this threshold based on your needs
    silence_duration = 1.5  # Duration of silence in seconds to stop recording
    silence_start = None

    while True:
        if not audio_queue.empty():
            audio_data = audio_queue.get()
            audio_level = np.abs(audio_data).mean()

            if recording:
                recorded_audio.append(audio_data)
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
                    recorded_audio = [audio_data]  # Start a new recording
                    print("Wakeword detected! Start recording...")

            print(f"Audio level: {audio_level} (recording: {recording})", end='\r')
