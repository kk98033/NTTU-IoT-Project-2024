import requests
from bs4 import BeautifulSoup

# 定義要爬取的URL列表
urls = [
    "https://theportalwiki.com/wiki/GLaDOS_voice_lines_(Portal)",
    "https://theportalwiki.com/wiki/GLaDOS_voice_lines_(Portal_2)"
]

def fetch_voice_lines(url):
    # 發送HTTP請求
    response = requests.get(url)

    # 確認請求成功
    if response.status_code == 200:
        # 解析HTML內容
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 找到包含對話的主要部分
        main_content = soup.find(id='mw-content-text')
        
        if main_content:
            # 提取所有的ul標籤
            ul_tags = main_content.find_all('ul')
            
            # 收集所有的對話
            voice_lines = []
            for ul in ul_tags:
                for li in ul.find_all('li'):
                    text = li.get_text()
                    # 只保留帶有引號的段落並去掉 "| Download | Play" 部分
                    if '"' in text:
                        clean_text = text.split('|')[0].strip()
                        voice_lines.append(clean_text)
            return voice_lines
        else:
            print(f"無法找到主要內容在 {url}")
    else:
        print(f"HTTP請求失敗，狀態碼: {response.status_code}，在 {url}")
    return []

# 打開文件以寫入
with open('GLaDOS_voice_lines.txt', 'w', encoding='utf-8') as file:
    # 遍歷所有URL並抓取對話
    for url in urls:
        voice_lines = fetch_voice_lines(url)
        for line in voice_lines:
            file.write(line + '\n')
    print("內容已保存到 GLaDOS_voice_lines.txt")
