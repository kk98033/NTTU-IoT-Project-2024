import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing_extensions import override
from openai import AssistantEventHandler
import requests

# 加載 .env 文件
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

import json

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
    for tool in run.required_action.submit_tool_outputs.tool_calls:
        if tool.function.name == "toggle_light":
            print('called function')
            tool_outputs.append({"tool_call_id": tool.id, "output": "電燈已開啟"})
        elif tool.function.name == "get_rain_probability":
                tool_outputs.append({
                "tool_call_id": tool.id,
                "output": "0.06"
            })
    
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
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        # print(messages) # type: SyncCursorPage[Message]
        response_dict = convert_response_to_dict(messages.json())
        # print(get_assistant_response(response_dict))
        return get_assistant_response(response_dict)
    else:
        print(run.status)

if __name__ == '__main__':
    assistant_id = "asst_CAnTShQDTVvObtJyPbNB04UP"
    thread = client.beta.threads.create()
    thread_id = thread.id  # 取得新創建的 thread 的 ID
    message_content = "你好，可以幫我開燈嗎？"

    # message_content = input()
    send_message_to_assistant(assistant_id, thread_id, message_content)