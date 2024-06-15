import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

from assistant_api_not_streaming import send_message_to_assistant

# 加載 .env 文件
load_dotenv()

# 從環境變數中取得 API 金鑰
api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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

def call_assistant_api(user_message, thread_id=None):
    if thread_id is None:
        global thread
        thread_id = thread.id
    return send_message_to_assistant(assistant_id, thread_id, user_message)

def call_tts_and_save(text, save_path):
    uri = f"http://127.0.0.1:9880/?text={text}&text_language=zh"
    stream_audio_from_api(uri, save_path)

def play_new_audio():
    response = requests.post('http://localhost:5000/switch_audio', json={'file': 'speech.mp3', 'type': 'mp3'})

    print(response.status_code, response.text)

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

assistant_id = "asst_CAnTShQDTVvObtJyPbNB04UP"
thread = client.beta.threads.create()
thread_id = thread.id  # 取得新創建的 thread 的 ID
if __name__ == '__main__':
    # message_content = "我想要聽SHIKANOKO NOKONOKO KOSHITANTAN一小時版本"
    message_content = "停止鬧鐘"

    # message_content = input()
    print(send_message_to_assistant(assistant_id, thread_id, message_content))
