import os
from openai import OpenAI
from dotenv import load_dotenv

# 加載 .env 文件
load_dotenv()

# 創建 OpenAI 客戶端實例
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 讀取 GLaDOS 說話腳本文件的內容
with open('GLaDOS_voice_lines.txt', 'r', encoding='utf-8') as file:
    glados_lines = file.read()

# 構建 system prompt，要求使用繁體中文回答
system_prompt = f"""你是 GLaDOS，一個來自《Portal》系列的人工智能。請用以下風格說話，並且所有回應都必須使用繁體中文：
{glados_lines}
"""

# 定義測試用的 user_prompts
user_prompts = [
    "你對測試對象有什麼看法？",
    "你認為人類有什麼缺點？",
    "如果測試失敗，你會怎麼處理？",
    "你覺得你的創造者怎麼樣？",
    "你最喜歡的測試是哪一個？",
    "你對測試結果有什麼意見？",
    "你認為你比人類聰明嗎？",
    "你有任何遺憾嗎？",
    "你為什麼要進行這些測試？",
    "如果你有機會逃脫，你會怎麼做？"
]

# 迭代所有的 user_prompts 並生成回應
for user_prompt in user_prompts:
    # 使用 OpenAI API 初始化 ChatGPT
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    # 打印 ChatGPT 的回應
    print(f"User Prompt: {user_prompt}")
    print(f"GLaDOS: {response.choices[0].message.content}\n")
