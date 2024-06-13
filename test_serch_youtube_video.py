from youtubesearchpython import VideosSearch
import requests

def search_youtube_and_play_first(query, api_url, max_results=1):
    # 搜尋 YouTube 影片
    videos_search = VideosSearch(query, limit=max_results)
    results = videos_search.result()['result']
    
    if results:
        first_video_url = results[0]['link']
        print(f"Playing video: {first_video_url}")

        # 發送 POST 請求來切換到 YouTube 影片
        response = requests.post(api_url, json={'file': first_video_url, 'type': 'youtube'})
        print(response.status_code, response.text)
    else:
        print("No videos found.")

search_query = "dead mom by nerrisa"
api_endpoint = 'http://localhost:5000/switch_audio'
search_youtube_and_play_first(search_query, api_endpoint)
