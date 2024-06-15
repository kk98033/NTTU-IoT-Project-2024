import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing_extensions import override
from openai import AssistantEventHandler
import json
import requests

from tools import call_beep, turn_mic_on, turn_mic_off, set_alarm_at, set_alarm, set_reminder, bedtime_procedure, home_procedure, outdoor_procedure, analyze_temperature_and_humidity, stop_music, turn_on_the_light, turn_off_the_light, search_google, get_weather_forecast, search_youtube_and_play_first

# 加載 .env 文件
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def process_tool_calls(required_action):
    tool_outputs = []

    tool_functions = {
        "turn_on_the_light": lambda tool: turn_on_the_light(),
        "turn_off_the_light": lambda tool: turn_off_the_light(),
        "stop_music": lambda tool: stop_music(),
        "outdoor_procedure": lambda tool: outdoor_procedure(),
        "set_reminder": lambda params: set_reminder(params['message'], params['delay']),
        "set_alarm": lambda params: set_alarm(params['time_to_ring']),
        "set_alarm_at": lambda params: set_alarm_at(params['month'], params['day'], params['hour'], params['minute']),
        "home_procedure": lambda params: home_procedure(params),
        "bedtime_procedure": lambda params: bedtime_procedure(params),
        "analyze_temperature_and_humidity": lambda tool: analyze_temperature_and_humidity(),
        "search_google": lambda params: search_google(params),
        "get_weather_forecast": lambda params: get_weather_forecast(),
        "search_youtube_and_play_first": lambda params: search_youtube_and_play_first(params)
    }

    # Loop through each tool in the required action section
    for tool in required_action.submit_tool_outputs.tool_calls:
        func = tool_functions.get(tool.function.name)
        print(tool.function.name)
        if func:
            try:
                # 解析參數
                params = json.loads(tool.function.arguments)
                print('params:', params)
                result = func(params)
                tool_outputs.append({"tool_call_id": tool.id, "output": result})
            except Exception as e:
                print(f"Failed to process tool {tool.function.name}: {e}")
    return tool_outputs



def convert_response_to_dict(api_response):
    # 將 API 回應轉換為 JSON 字典
    response_dict = json.loads(api_response)
    return response_dict

def get_assistant_response(response_dict):
    # 提取 assistant 的回應文字
    for message in response_dict['data']:
        if message['role'] == 'assistant':
            for content_block in message['content']:
                if content_block['type'] == 'text':
                    return content_block['text']['value']
    return None

def send_message_to_assistant(assistant_id, thread_id, message_content):
    # 取得 Assistant
    assistant = client.beta.assistants.retrieve(assistant_id)

    print(thread_id)
    # 傳送訊息給 Assistant
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_content,
    )
    print(message)

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )
 
    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        # print(messages) # type: SyncCursorPage[Message]
        response_dict = convert_response_to_dict(messages.json())
        # print(get_assistant_response(response_dict))
        return get_assistant_response(response_dict)
    else:
        print(run.status)
 
    # Define the list to store tool outputs
    tool_outputs = []
    
    # Loop through each tool in the required action section
    tool_outputs = process_tool_calls(run.required_action)
    # for tool in run.required_action.submit_tool_outputs.tool_calls:
        # if tool.function.name == "toggle_light":
        #     print('called function')
        #     tool_outputs.append({"tool_call_id": tool.id, "output": "電燈已開啟"})
        # elif tool.function.name == "get_rain_probability":
        #         tool_outputs.append({
        #         "tool_call_id": tool.id,
        #         "output": "0.06"
        #     })
    
    # Submit all tool outputs at once after collecting them in a list
    if tool_outputs:
        try:
            run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            print("Tool outputs submitted successfully.")
        except Exception as e:
            print("Failed to submit tool outputs:", e)
    else:
        print("No tool outputs to submit.")
        
    if run.status == 'completed':
        print('completed')
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        # print(messages) # type: SyncCursorPage[Message]
        response_dict = convert_response_to_dict(messages.json())
        # print(get_assistant_response(response_dict))
        return get_assistant_response(response_dict)
    else:
        print('not completed')
        print(run.status)

if __name__ == '__main__':
    assistant_id = "asst_CAnTShQDTVvObtJyPbNB04UP"
    thread = client.beta.threads.create()
    thread_id = thread.id  # 取得新創建的 thread 的 ID
    # message_content = "我想要聽SHIKANOKO NOKONOKO KOSHITANTAN一小時版本"
    message_content = "一分鐘後提醒我倒垃圾"

    # message_content = input()
    print(send_message_to_assistant(assistant_id, thread_id, message_content))
