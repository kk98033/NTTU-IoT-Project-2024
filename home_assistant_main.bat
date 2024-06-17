@echo off
REM 進入虛擬環境並執行 home_assistant_main.py

REM 切換到專案目錄
cd /d "D:\物聯網專案\NTTU-IoT-Project-2024"

REM 激活虛擬環境
call myenv\Scripts\activate.bat

REM 確保當前在虛擬環境中，檢查是否已經成功進入虛擬環境
if not defined VIRTUAL_ENV (
    echo 未能成功進入虛擬環境
    pause
    exit /b
)

REM 執行 Python 腳本
python .\home_assistant_main.py

REM 保持窗口開啟以查看輸出
pause
