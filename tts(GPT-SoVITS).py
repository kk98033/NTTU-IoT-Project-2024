import requests

def call_tts_and_save(text, save_path):
    uri = f"http://210.240.160.27:9880/?text={text}&text_language=zh"
    stream_audio_from_api(uri, save_path)

def stream_audio_from_api(uri, save_path):
    try:
        print('streaming')
        # 增加超時設定
        response = requests.get(uri, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(save_path, 'wb') as audio_file:
            for chunk in response.iter_content(chunk_size=8192):
                audio_file.write(chunk)
        
        print(f"Audio saved to {save_path}")
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"General error: {e}")

output_audio = 'output.ogg'
call_tts_and_save("你好啊", output_audio)
