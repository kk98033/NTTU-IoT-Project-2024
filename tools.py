# tools.py

import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# load .env file
load_dotenv()

# get API key from .env file
os.environ["google_search_api_key"] = os.getenv('google_search_api_key')

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

def call_beep():
    payload = {
        'beep': '1',
    }
    return call_node_red_api('beep', payload)

def turn_mic_on():
    payload = {
        'mic': 'on',
    }
    return call_node_red_api('mic_on', payload)

def turn_mic_off():
    payload = {
        'mic': 'off',
    }
    return call_node_red_api('mic_off', payload)

def search_google(parameters):
    query = parameters['query']

    def web_search(keyword: str) -> str:
        """根據給定的關鍵字進行網頁搜尋並返回搜尋結果的主要文字內容。(keyword 只能輸入中文)"""
        urls = get_search_url(keyword=keyword)
        print(urls)
        result = f'[使用"**繁體中文**"回答，以下是"{keyword}"的搜索部分]:\n'
        for i, url in enumerate(urls):
            if not url.lower().endswith('.pdf'):
                result += f'文章{i+1}:\n"""'
                result += crawl_webpage(url) + '"""\n'
        print(len(result))
        return result
        
    def get_search_url(keyword):
        url = f"https://www.googleapis.com/customsearch/v1?key={os.environ['google_search_api_key']}&cx=013036536707430787589:_pqjad5hr1a&q={keyword}&cr=countryTW&num=3"
        response = requests.get(url)
        if response.status_code == 200:
            search_results = response.json()
            links = [item['link'] for item in search_results.get('items', [])]
            return links
        else:
            print("Error occurred while fetching search results")
            return []

    def crawl_webpage(url):
        try:
            response = requests.get(url, verify=False)  # Disabling SSL verification
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                main_content = soup.find("div", class_="main-content")
                if not main_content:
                    main_content = soup

                for elem in main_content.find_all(["nav", "footer", "sidebar", "script", "noscript"]):
                    elem.extract()

                lines = main_content.get_text().strip().splitlines()
                text_content = '\n'.join(line for line in lines if line.strip())
                return text_content
            else:
                print("Failed to fetch webpage")
                return ""
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return ""
    result = web_search(query)
    return result

def get_weather_info(location):
    payload = {
        'location': location,
    }
    return call_node_red_api('get_weather', payload)

def play_music_track(song):
    payload = {
        'song': song,
    }
    return call_node_red_api('play_music', payload)
