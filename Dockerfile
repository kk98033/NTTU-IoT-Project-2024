# 使用 Python 官方映像作為基礎映像
FROM python:3.12-slim

# 設定工作目錄
WORKDIR /app

# 複製專案中的所有文件到容器中
COPY . .

# 安裝依賴包並升級 pip
RUN python -m venv venv
RUN ./venv/bin/pip install --upgrade pip

# 手動安裝 PyTorch 及其依賴
RUN ./venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安裝 requirements.txt 中的其餘依賴包
RUN ./venv/bin/pip install -r requirements.txt

# 設定虛擬環境變量
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 執行所有的 .py 文件
CMD ["/bin/bash", "-c", "source /app/venv/bin/activate && python get_max9814_mic.py & python home_assistant_main.py & python home_assistant_speaker_server.py & python reminder_server.py"]
