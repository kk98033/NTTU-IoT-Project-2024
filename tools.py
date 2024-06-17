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
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

sheet_id = '1_PZkF4x315FKZqo1m74XvjLMYuB6yXl_fNtfFnbSbVY'
credentials_file = 'credentials.json'

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

def change_mini_screen(screen_index):
    client.publish("change_mini_screen", screen_index)

def get_today_date():
    today = datetime.today()
    date_info = {
        "year": today.year,
        "month": today.month,
        "day": today.day
    }
    return json.dumps(date_info)

def turn_on_the_light():
    payload = {
        'switch': 'ON',
    }
    call_node_red_api('turn_on_the_light', payload)
    return "已經開啟電燈開關"

def turn_off_the_light():
    payload = {
        'switch': 'OFF',
    }
    call_node_red_api('turn_off_the_light', payload)
    return "已經關閉電燈開關"

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
        first_video = results[0]
        first_video_url = first_video['link']
        first_video_title = first_video['title']
        print(f"Playing video: {first_video_title} ({first_video_url})")

        # 發送 POST 請求來切換到 YouTube 影片
        response = requests.post(api_url, json={'file': first_video_url, 'type': 'youtube'})
        print(response.status_code, response.text)
        return f"即將播放：{first_video_title}"
    else:
        print("No videos found.")
        return "No videos found."

def play_youtube_url(url):
    api_url='http://localhost:5000/switch_audio'
    print(url)
    response = requests.post(api_url, json={'file': url, 'type': 'youtube'})
    print(response.status_code, response.text)
    return f"即將播放音樂"

def get_latest_coordinates_from_sheet(sheet_id, credentials_file, sheet_name="GPS"):
    # 使用憑證文件進行認證
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(credentials)

    # 讀取指定的 Google Sheets 表單和工作表
    sheet = client.open_by_key(sheet_id).worksheet(sheet_name)

    # 取得所有資料列
    rows = sheet.get_all_values()

    if not rows:
        return None, None

    # 取得最新的一行資料
    latest_row = rows[-1]

    print("最新的一行資料:", latest_row)  # 打印最新的一行資料進行調試

    # 日期 | 時間 | 緯度 | 經度
    try:
        latitude = float(latest_row[2])
        longitude = float(latest_row[3])
    except (ValueError, IndexError):
        return None, None

    return latitude, longitude


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
    # latitude = 25.0330
    # longitude = 121.5654
    latest_latitude, latest_longitude = get_latest_coordinates_from_sheet(sheet_id, credentials_file)
    print(latest_latitude, latest_longitude)
    # 獲取縣市和區域信息
    city, district = get_location(google_maps_api_key, latest_latitude, latest_longitude)
    city = city.replace('台', '臺')
    # print(f"這個位置在台灣的: {city} {district}")
    
    # 如果成功獲取縣市信息，則查詢天氣預報
    if city:
        weather_info = call_weather_forecast_API(city=city)
        if weather_info:
            parsed_data = parse_latest_weather_data(weather_info)
            weather_json = json.dumps(parsed_data, ensure_ascii=False, indent=4)
            
            # 呼叫 Node-RED API 更新天氣
            payload = {'weather': weather_json}
            print(payload)
            call_node_red_api('update_weather', payload)
            
            return weather_json
        else:
            return "Failed to retrieve weather data"
    else:
        return "Failed to retrieve location information"


def stop_music():
    url = 'http://localhost:5000/stop_youtube'
    response = requests.post(url)
    if response.status_code == 200:
        return 'YouTube video stopped successfully.'
    else:
        return f'Failed to stop YouTube video. Status code: {response.status_code}'

def set_reminder(message, delay):
    url = 'http://localhost:6669/set_reminder'
    payload = {'message': message, 'delay': delay}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    response_json = response.json()
    message = response_json.get('message') 
    # print(message)  
    return message  

def set_alarm(time_to_ring):
    url = 'http://localhost:6669/set_alarm'
    payload = {'time_to_ring': time_to_ring}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    response_json = response.json()
    message = response_json.get('message') 
    # print(message)  
    return message  

def set_alarm_at(month, day, hour, minute):
    url = 'http://localhost:6669/set_alarm_at'
    payload = {'month': month, 'day': day, 'hour': hour, 'minute': minute}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    response_json = response.json()
    message = response_json.get('message') 
    # print(message)  
    return message  

def analyze_temperature_and_humidity(date=None):
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1_PZkF4x315FKZqo1m74XvjLMYuB6yXl_fNtfFnbSbVY/edit?gid=0#gid=0"
    credentials_file = "credentials.json"

    # 設定憑證檔案和範圍
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)

    # 讀取 Google Sheet
    spreadsheet = client.open_by_url(spreadsheet_url)

    # 讀取 "溫度" 表單
    worksheet_temp = spreadsheet.worksheet("溫度")
    data_temp = worksheet_temp.get_all_values()

    # 讀取 "濕度" 表單
    worksheet_humidity = spreadsheet.worksheet("濕度")
    data_humidity = worksheet_humidity.get_all_values()

    # 轉換為 DataFrame，並手動設定欄位名稱
    df_temp = pd.DataFrame(data_temp[1:], columns=['日期', '時間', '溫度'])
    df_humidity = pd.DataFrame(data_humidity[1:], columns=['日期', '時間', '濕度'])

    # 確認日期和數值格式
    df_temp['日期'] = pd.to_datetime(df_temp['日期'], format='%Y-%m-%d').dt.date
    df_temp['溫度'] = pd.to_numeric(df_temp['溫度'])

    df_humidity['日期'] = pd.to_datetime(df_humidity['日期'], format='%Y-%m-%d').dt.date
    df_humidity['濕度'] = pd.to_numeric(df_humidity['濕度'])

    # 如果沒有提供日期，則使用今日日期
    if date is None:
        date = datetime.now().date()

    # 只選擇指定日期的資料
    temp_data = df_temp[df_temp['日期'] == date]
    humidity_data = df_humidity[df_humidity['日期'] == date]

    # 分析結果字典
    result = {
        "日期": str(date),
        "溫度分析": {},
        "濕度分析": {}
    }

    # 分析溫度
    if not temp_data.empty:
        avg_temp = temp_data['溫度'].mean().astype(float)
        max_temp = temp_data['溫度'].max().astype(float)
        min_temp = temp_data['溫度'].min().astype(float)

        result["溫度分析"] = {
            '平均溫度': avg_temp,
            '最高溫度': max_temp,
            '最低溫度': min_temp,
        }
    else:
        result["溫度分析"] = "指定日期沒有溫度資料。"

    # 分析濕度
    if not humidity_data.empty:
        avg_humidity = humidity_data['濕度'].mean().astype(float)
        max_humidity = humidity_data['濕度'].max().astype(float)
        min_humidity = humidity_data['濕度'].min().astype(float)

        result["濕度分析"] = {
            '平均濕度': avg_humidity,
            '最高濕度': max_humidity,
            '最低濕度': min_humidity,
        }
    else:
        result["濕度分析"] = "指定日期沒有濕度資料。"

    return json.dumps(result, ensure_ascii=False, indent=4)

''' procedures '''
def list_reminders():
    response = requests.get('http://localhost:6669/list_reminders')
    if response.status_code == 200:
        return response.json().get('reminders', [])
    else:
        return []
    
def outdoor_procedure():
    procedure_text = '出門流程已經啟動(一定要說你做了什麼)，已經幫忙完成：'
    
    # 撥動電燈開關
    turn_off_the_light()
    procedure_text += '1.關燈'

    # 列出目前的提醒事項
    procedure_text += '2.提醒事項'
    reminders = list_reminders()
    procedure_text += "目前的提醒事項:"
    for reminder in reminders:
        procedure_text += f'{reminder}\n'

    print(procedure_text)
    return procedure_text


def home_procedure(music_name):
    procedure_text = '回家流程已啟動(一定要說你做了什麼)，已經幫忙完成：'
    # 撥動電燈開關
    turn_on_the_light()
    procedure_text += '1.開燈'

    # 播放回家提示音樂
    procedure_text += '2.播放了一首音樂'
    procedure_text += play_youtube_url(music_name)

    print(procedure_text)
    return procedure_text


def bedtime_procedure(music_name):
    procedure_text = '睡覺流程已啟動(一定要說你做了什麼)，已經幫忙完成：'

    # 撥動電燈開關
    turn_off_the_light()
    procedure_text += '1.關燈'

    # 播放睡覺提示音樂
    procedure_text += '2.播放了一首睡覺音樂'
    # procedure_text += search_youtube_and_play_first(music_name)
    procedure_text += play_youtube_url('3VAIjXvUvbI')

    # 列出目前的提醒事項
    reminders = list_reminders()
    print("目前的提醒事項:")
    procedure_text += "目前的提醒事項:"
    for reminder in reminders:
        procedure_text += f'{reminder}\n'

    # 設置鬧鐘
    procedure_text += set_alarm(28800)

    print(procedure_text)
    return procedure_text

def send_weather_data():
    # 定義資料
    data = {
        "Wx": "雲, 22",
        "PoP": "30, 百分比",
        "MinT": "27, C",
        "CI": "舒適至易中暑",
        "MaxT": "23, C"
    }
    # 將資料轉換為 JSON 格式
    payload = json.dumps(data)
    
    # 設置 MQTT 客戶端
    client = mqtt.Client()
    
    mqtt_server = "34.168.176.224"

    # 連接到 MQTT 服務器
    client.connect(mqtt_server, 1883, 60)
    
    # 發佈消息到指定的 topic
    client.publish("weather", payload)
    
    # 斷開連接
    client.disconnect()



if __name__ == '__main__':
    # print(turn_on_the_light())
    # print(turn_off_the_light())
    # print(get_today_date())
    # print(turn_mic_on())
    # print(turn_mic_off())

    # latest_latitude, latest_longitude = get_latest_coordinates_from_sheet(sheet_id, credentials_file)
    # print(latest_latitude, latest_longitude)
    # print(get_weather_forecast())
    # print(bedtime_procedure('a'))
    print(home_procedure('a'))
    # print(analyze_temperature_and_humidity())

    # stop_music()

    # turn_mic_on()
    # time.sleep(1)  # 等待訊息發送完成
    # turn_mic_off()
    # time.sleep(1)  # 等待訊息發送完成

    # toggle_switch()