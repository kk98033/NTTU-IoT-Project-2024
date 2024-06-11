# assistant_api.py

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

class EventHandler(AssistantEventHandler):
    @override
    def on_event(self, event):
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, run_id)
 
    def handle_requires_action(self, data, run_id):
        tool_outputs = []
        
        for tool in data.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "toggle_light":
                print('called function')
                tool_outputs.append({"tool_call_id": tool.id, "output": "電燈已開啟"})
            elif tool.function.name == "get_rain_probability":
                tool_outputs.append({"tool_call_id": tool.id, "output": "0.06"})
        
        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)
 
    def submit_tool_outputs(self, tool_outputs, run_id):
        with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(),
        ) as stream:
            for text in stream.text_deltas:
                print(text, end="", flush=True)
            print()

def send_message_to_assistant(assistant_id, thread_id, message_content):
    # 初始化 EventHandler
    event_handler = EventHandler()

    # 取得 Assistant
    assistant = client.beta.assistants.retrieve(assistant_id)

    # 傳送訊息給 Assistant
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_content,
    )
    print(message)

    # 使用 stream 來處理 Assistant 的回應
    with client.beta.threads.runs.stream(
        thread_id=thread_id,
        assistant_id=assistant.id,
        event_handler=event_handler
    ) as stream:
        stream.until_done()

