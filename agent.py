# main.py

import os
from openai import OpenAI
from dotenv import load_dotenv
# from assistant_api import send_message_to_assistant # streaming
from assistant_api_not_streaming import send_message_to_assistant

# 加載 .env 文件
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

assistant_id = "asst_CAnTShQDTVvObtJyPbNB04UP"
thread = client.beta.threads.create()
thread_id = thread.id  # 取得新創建的 thread 的 ID
message_content = "你好，可以幫我開燈嗎？"

# message_content = input()
send_message_to_assistant(assistant_id, thread_id, message_content)
