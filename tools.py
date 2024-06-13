# tools.py

import requests

def call_node_red_api(endpoint, payload):
    url = f'http://127.0.0.1:1880/{endpoint}'
    
    print(f'準備呼叫 Node-RED API: {url}...')
    
    try:
        response = requests.post(url, json=payload, timeout=10)  # 設定超時為 10 秒
        print('API 請求已發送...')
    except requests.Timeout:
        print('呼叫 API 超時。請確認 Node-RED 伺服器是否在運行。')
        return None
    except requests.ConnectionError:
        print('無法連接到 Node-RED 伺服器。請檢查伺服器是否在運行，以及網路設置是否正確。')
        return None
    except Exception as e:
        print(f'呼叫 API 時出現未知錯誤: {e}')
        return None

    # 處理回應
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print('回應不是 JSON 格式:', response.text)
            return None
    else:
        print('Failed to call Node-RED API:', response.status_code)
        return None

def beep():
    payload = {
        'beep': '1',
    }
    result = call_node_red_api('beep', payload)
    if result:
        print('Result:', result)
    else:
        print('呼叫 Node-RED API 失敗。')

def mic_on():
    payload = {
        'mic': 'on',
    }
    result = call_node_red_api('mic_on', payload)
    if result:
        print('Result:', result)
    else:
        print('呼叫 Node-RED API 失敗。')

def mic_off():
    payload = {
        'mic': 'off',
    }
    result = call_node_red_api('mic_off', payload)
    if result:
        print('Result:', result)
    else:
        print('呼叫 Node-RED API 失敗。')

def google_search(query):
    payload = {
        'query': query,
    }
    result = call_node_red_api('google_search', payload)
    if result:
        print('Result:', result)
    else:
        print('呼叫 Node-RED API 失敗。')

def get_weather(location):
    payload = {
        'location': location,
    }
    result = call_node_red_api('get_weather', payload)
    if result:
        print('Result:', result)
    else:
        print('呼叫 Node-RED API 失敗。')

def play_music(song):
    payload = {
        'song': song,
    }
    result = call_node_red_api('play_music', payload)
    if result:
        print('Result:', result)
    else:
        print('呼叫 Node-RED API 失敗。')
