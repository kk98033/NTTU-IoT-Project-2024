import os

# 加載 .env 文件
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

response = client.audio.speech.create(
    model="tts-1",
    voice="nova",
    input="Hello world! This is a streaming test.",
)

response.stream_to_file("output.mp3")