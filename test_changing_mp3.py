import requests

# # 發送 POST 請求來切換音頻文件
# response = requests.post('http://localhost:5000/switch_audio', json={'file': 'speech.mp3', 'type': 'mp3'})
# print(response.status_code, response.text)

# 發送 POST 請求來切換到 YouTube 影片
response = requests.post('http://localhost:5000/switch_audio', json={'file': 'https://youtu.be/tL9yDq5hpgI?si=p8uDIFuSafOd7yfy', 'type': 'youtube'})
print(response.status_code, response.text)