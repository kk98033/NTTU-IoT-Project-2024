import requests
import json

def call_set_reminder(message, delay):
    url = 'http://localhost:6669/set_reminder'
    payload = {'message': message, 'delay': delay}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()

def call_set_alarm(time_to_ring):
    url = 'http://localhost:6669/set_alarm'
    payload = {'time_to_ring': time_to_ring}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()

def call_set_alarm_at(month, day, hour, minute):
    url = 'http://localhost:6669/set_alarm_at'
    payload = {'month': month, 'day': day, 'hour': hour, 'minute': minute}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()

# 測試呼叫
print(call_set_reminder("Time to work!", 60))
print(call_set_alarm(300))
print(call_set_alarm_at(6, 15, 8, 0))
