import requests

response = requests.post('http://localhost:5000/switch_audio', json={'file': 'speech.mp3'})
print(response.status_code, response.text)
