# tools.py

import requests
from datetime import datetime
from bs4 import BeautifulSoup
import os
import json
import time
from dotenv import load_dotenv
from youtubesearchpython import VideosSearch
import paho.mqtt.client as mqtt

# load .env file
load_dotenv()

# get API key from .env file
os.environ["google_search_api_key"] = os.getenv('google_search_api_key')

# MQTT 設定
MQTT_BROKER = "34.168.176.224"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 60

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully!")
    else:
        print(f"Connection failed with code {rc}")

def on_publish(client, userdata, mid):
    print("Message published")

# 設定回調函數
client.on_connect = on_connect
client.on_publish = on_publish

# 連接 MQTT 伺服器
client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
client.loop_start()


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
    client.publish("mic_on", "on")

def turn_mic_off():
    client.publish("mic_off", "off")

def toggle_switch():
    ''' 用於開啟/關閉房間電燈開關 '''
    payload = {
        'switch': 'toggle',
    }
    call_node_red_api('toggle_switch', payload)
    
    return "已經撥動電燈開關"

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

def search_youtube_and_play_first(parameters):
    max_results=1
    api_url='http://localhost:5000/switch_audio'
    query = parameters['query']
    
    # 搜尋 YouTube 影片
    videos_search = VideosSearch(query, limit=max_results)
    results = videos_search.result()['result']
    
    if results:
        first_video_url = results[0]['link']
        print(f"Playing video: {first_video_url}")

        # 發送 POST 請求來切換到 YouTube 影片
        response = requests.post(api_url, json={'file': first_video_url, 'type': 'youtube'})
        print(response.status_code, response.text)
        return first_video_url
    else:
        print("No videos found.")
        return "No videos found."

def get_weather_forecast():
    def get_location(api_key, lat, lng):
        # 建立請求的 URL
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={api_key}&language=zh-TW"
        
        # 發送請求到 Geocoding API
        response = requests.get(url)
        
        # 獲取返回的 JSON 資料
        data = response.json()
        
        city = None
        district = None
        
        # 檢查是否有有效的返回結果
        if data['status'] == 'OK':
            # 遍歷返回結果的地址組件，查找縣市和區域信息
            for component in data['results'][0]['address_components']:
                if 'administrative_area_level_1' in component['types']:
                    city = component['long_name']
                if 'administrative_area_level_3' in component['types']:
                    district = component['long_name']
            return city, district
        else:
            return None, None

    def call_weather_forecast_API(city="臺東縣"):
        url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
        params = {
            "Authorization": os.getenv('WEATHER_API_KEY'),
            "locationName": city
        }

        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            # print(data)
            return data
        else:
            return None


    def parse_latest_weather_data(weather_info):
        locations_data = []

        locations = weather_info.get('records', {}).get('location', [])
        for loc in locations:
            location_data = {
                "locationName": loc.get('locationName', ''),
                "weatherElements": []
            }

            for element in loc.get('weatherElement', []):
                latest_time_info = max(
                    element.get('time', []),
                    key=lambda x: datetime.strptime(x['startTime'], '%Y-%m-%d %H:%M:%S') if x.get('startTime') else datetime.min
                )

                element_data = {
                    "elementName": element.get('elementName', ''),
                    "description": element.get('description', ''),
                    "latestTime": latest_time_info.get('startTime', ''),
                    "endTime": latest_time_info.get('endTime', ''),
                    "dataTime": latest_time_info.get('dataTime', ''),
                    "parameter": latest_time_info.get('parameter', {})
                }

                location_data["weatherElements"].append(element_data)

            locations_data.append(location_data)

        return {
            "datasetDescription": weather_info.get('records', {}).get('datasetDescription', ''),
            "locationsName": weather_info.get('records', {}).get('locationsName', ''),
            "locationsData": locations_data
        }

    # 你的 Google Maps API 金鑰
    google_maps_api_key = os.getenv('GOOGLE_MAP_API_KEY')
    
    # TODO: 使用 mqtt server 最新的經緯度資訊：
    latitude = 25.0330
    longitude = 121.5654
    
    # 獲取縣市和區域信息
    city, district = get_location(google_maps_api_key, latitude, longitude)
    city = city.replace('台', '臺')
    # print(f"這個位置在台灣的: {city} {district}")
    
    # 如果成功獲取縣市信息，則查詢天氣預報
    if city:
        weather_info = call_weather_forecast_API(city=city)
        if weather_info:
            parsed_data = parse_latest_weather_data(weather_info)
            return json.dumps(parsed_data, ensure_ascii=False, indent=4)
        else:
            return "Failed to retrieve weather data"
    else:
        return "Failed to retrieve location information"

def play_music_track(song):
    payload = {
        'song': song,
    }
    return call_node_red_api('play_music', payload)

if __name__ == '__main__':
    turn_mic_on()
    time.sleep(1)  # 等待訊息發送完成
    turn_mic_off()
    time.sleep(1)  # 等待訊息發送完成

    # toggle_switch()